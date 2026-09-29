import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_DIR / "input"

INPUT_DIR.mkdir(exist_ok=True)


def download_video(url):
    output_template = str(INPUT_DIR / "downloaded.%(ext)s")

    command = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--no-playlist",
        "-f",
        "bv*+ba/b",
        "--merge-output-format",
        "mp4",
        "--remux-video",
        "mp4",
        "-o",
        output_template,
        url,
    ]

    print("\nDownloading video...\n")

    result = subprocess.run(command)

    if result.returncode == 0:
        print("\nDownload complete!")
        print(f"Saved in: {INPUT_DIR}")
    else:
        print("\nDownload failed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("python scripts/download_video.py VIDEO_URL")
        sys.exit(1)

    url = sys.argv[1]
    download_video(url)
    