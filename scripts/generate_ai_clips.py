from pathlib import Path
import json
import subprocess
import os

INPUT_VIDEO = Path(
    os.environ.get("AICLIPPER_INPUT", "input/current.mp4")
)
AI_CLIPS = Path("output/ai_clips.json")
OUTPUT_DIR = Path("output/ai_generated")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

data = json.loads(AI_CLIPS.read_text(encoding="utf-8"))

clips = data["clips"]

print(f"Found {len(clips)} AI-selected clips.")

for index, clip in enumerate(clips, start=1):

    start = clip["start"]
    end = clip["end"]

    output_file = OUTPUT_DIR / f"clip_{index:02d}.mp4"

    print(
        f"\nCreating Clip {index}: "
        f"{start}s → {end}s"
    )

    command = [
        "ffmpeg",
        "-y",
        "-ss", str(start),
        "-i", str(INPUT_VIDEO),
        "-to", str(end - start),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(output_file)
    ]

    subprocess.run(command, check=True)

    print(f"Saved: {output_file}")

print("\nDone! 🎉")
print(f"Clips saved in: {OUTPUT_DIR}")