from pathlib import Path
import subprocess

VIDEO = Path("input/test.mp4")
CLIPS_FILE = Path("output/clips.txt")
OUTPUT_DIR = Path("output/clips")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

clips = []

with open(CLIPS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        number, start, end = line.strip().split("|")

        clips.append({
            "number": int(number),
            "start": float(start),
            "end": float(end)
        })


for clip in clips:

    number = clip["number"]
    start = clip["start"]
    end = clip["end"]

    duration = end - start

    output_file = OUTPUT_DIR / f"clip_{number:02d}.mp4"

    print(
        f"\nCreating Clip {number}: "
        f"{start:.2f}s → {end:.2f}s"
    )

    command = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", str(VIDEO),
        "-t", str(duration),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-preset", "fast",
        str(output_file)
    ]

    subprocess.run(command, check=True)

    print(f"Saved: {output_file}")


print("\n🔥 ALL CLIPS CREATED!")
print(f"Check: {OUTPUT_DIR}")