import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "input"

INPUT_DIR.mkdir(exist_ok=True)


def detect_platform(url):
    hostname = urlparse(url).hostname or ""
    hostname = hostname.lower()

    if "youtube.com" in hostname or "youtu.be" in hostname:
        return "YouTube"

    if "tiktok.com" in hostname:
        return "TikTok"

    if "instagram.com" in hostname:
        return "Instagram"

    if "facebook.com" in hostname or "fb.watch" in hostname:
        return "Facebook"

    return "Other"


def download_video(url):
    platform = detect_platform(url)

    print(f"\nPlatform detected: {platform}")
    print("Downloading best quality available...\n")

    # Use the video's title + ID so every download gets its own filename.
    output_template = str(
        INPUT_DIR / "%(title)s [%(id)s].%(ext)s"
    )

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
    ]

    # YouTube workaround
    if platform == "YouTube":
        command += [
            "--extractor-args",
            "youtube:player_client=web_embedded",
        ]

    command += [
        "--no-playlist",

        # Best video + best audio available.
        " -f" if False else "-f",
        "bv*+ba/b",

        "--merge-output-format",
        "mp4",

        "--remux-video",
        "mp4",

        "-o",
        output_template,

        url,
    ]

    print("Starting download...\n")

    result = subprocess.run(command)

    if result.returncode == 0:
        print("\n✅ Download complete!")
        print(f"📁 Saved inside: {INPUT_DIR}")
    else:
        print("\n❌ Download failed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print('python scripts/download_video.py "VIDEO_URL"')
        sys.exit(1)

    download_video(sys.argv[1])