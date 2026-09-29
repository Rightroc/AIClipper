import subprocess
import sys
import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"
INPUT_DIR = PROJECT_DIR / "input"


INPUT_DIR.mkdir(exist_ok=True)


def run_script(script_name, env):
    script_path = SCRIPTS_DIR / script_name

    print("\n" + "=" * 60)
    print(f"RUNNING: {script_name}")
    print("=" * 60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_DIR,
        env=env
    )

    if result.returncode != 0:
        print(f"\n❌ {script_name} failed.")
        sys.exit(result.returncode)

    print(f"\n✅ {script_name} completed.")


def main():
    if len(sys.argv) < 2:
        print('Usage:')
        print('python ai_clipper.py "VIDEO_URL"')
        sys.exit(1)

    url = sys.argv[1]

    print("\n" + "=" * 60)
    print("                 AI CLIPPER")
    print("=" * 60)

    # --------------------------------------------------
    # 1. DOWNLOAD VIDEO
    # --------------------------------------------------

    print("\nDownloading source video...")

    download_script = SCRIPTS_DIR / "download_video.py"

    result = subprocess.run(
        [sys.executable, str(download_script), url],
        cwd=PROJECT_DIR
    )

    if result.returncode != 0:
        print("\n❌ Download failed.")
        sys.exit(result.returncode)

    # --------------------------------------------------
    # 2. FIND NEWEST VIDEO
    # --------------------------------------------------

    videos = [
        video
        for video in INPUT_DIR.glob("*.mp4")
        if video.name != "current.mp4"
    ]

    if not videos:
        print("\n❌ No downloaded video found.")
        sys.exit(1)

    source_video = max(
        videos,
        key=lambda video: video.stat().st_mtime
    )

    print("\n🎬 Source video:")
    print(source_video.name)

    # --------------------------------------------------
    # 3. TELL PIPELINE WHICH VIDEO TO PROCESS
    # --------------------------------------------------

    env = os.environ.copy()
    env["AICLIPPER_INPUT"] = str(source_video)

    print("\n📌 Processing:")
    print(source_video)

    # --------------------------------------------------
    # 4. RUN AI PIPELINE
    # --------------------------------------------------

    run_script("transcribe.py", env)
    run_script("ai_clip_finder.py", env)
    run_script("generate_ai_clips.py", env)
    run_script("add_captions.py", env)

    # --------------------------------------------------
    # 5. DONE
    # --------------------------------------------------

    print("\n" + "=" * 60)
    print("             🎉 AI CLIPPER COMPLETE")
    print("=" * 60)

    print("\nFinal clips:")
    print(PROJECT_DIR / "output" / "final")


if __name__ == "__main__":
    main()