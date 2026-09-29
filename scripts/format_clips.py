from pathlib import Path
import subprocess
import re

CLIP_DIR = Path("output/clips")
CLIPS_FILE = Path("output/clips.txt")
FULL_SRT = Path("output/subtitles.srt")
OUTPUT_DIR = Path("output/final")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def srt_to_seconds(timestamp):
    h, m, s = timestamp.split(":")
    s, ms = s.split(",")

    return (
        int(h) * 3600
        + int(m) * 60
        + int(s)
        + int(ms) / 1000
    )


def seconds_to_srt(seconds):

    if seconds < 0:
        seconds = 0

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))

    if milliseconds >= 1000:
        secs += 1
        milliseconds = 0

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


# Read clip timestamps
clips = []

with open(CLIPS_FILE, "r", encoding="utf-8") as f:

    for line in f:

        number, start, end = line.strip().split("|")

        clips.append({
            "number": int(number),
            "start": float(start),
            "end": float(end)
        })


# Read full SRT
srt_text = FULL_SRT.read_text(encoding="utf-8")

blocks = re.split(r"\n\s*\n", srt_text.strip())

subtitles = []

for block in blocks:

    lines = block.splitlines()

    if len(lines) < 3:
        continue

    timing = lines[1]

    start_text, end_text = timing.split(" --> ")

    start = srt_to_seconds(start_text)
    end = srt_to_seconds(end_text)

    text = "\n".join(lines[2:])

    subtitles.append({
        "start": start,
        "end": end,
        "text": text
    })


for clip in clips:

    number = clip["number"]
    clip_start = clip["start"]
    clip_end = clip["end"]

    print(f"\nProcessing Clip {number}...")

    # Create subtitle file specifically for this clip
    clip_srt = OUTPUT_DIR / f"clip_{number:02d}.srt"

    with open(clip_srt, "w", encoding="utf-8") as f:

        subtitle_number = 1

        for subtitle in subtitles:

            # Ignore subtitles completely outside the clip
            if subtitle["end"] <= clip_start:
                continue

            if subtitle["start"] >= clip_end:
                continue

            # Shift subtitle timestamps so clip begins at 0
            new_start = max(
                0,
                subtitle["start"] - clip_start
            )

            new_end = min(
                clip_end - clip_start,
                subtitle["end"] - clip_start
            )

            if new_end <= new_start:
                continue

            f.write(f"{subtitle_number}\n")
            f.write(
                f"{seconds_to_srt(new_start)} --> "
                f"{seconds_to_srt(new_end)}\n"
            )
            f.write(f"{subtitle['text']}\n\n")

            subtitle_number += 1


    output_file = OUTPUT_DIR / f"clip_{number:02d}.mp4"

    # Windows/FFmpeg subtitle path
    subtitle_path = str(clip_srt.resolve())
    subtitle_path = subtitle_path.replace("\\", "/")
    subtitle_path = subtitle_path.replace(":", "\\:")

    # Cleaner subtitle style
    filter_complex = (
        "scale=1080:1920:"
        "force_original_aspect_ratio=increase,"
        "crop=1080:1920,"
        f"subtitles='{subtitle_path}':"
        "force_style='"
        "FontName=Arial,"
        "FontSize=12,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=1,"
        "Alignment=2,"
        "MarginV=220"
        "'"
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(CLIP_DIR / f"clip_{number:02d}.mp4"),
        "-vf",
        filter_complex,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_file)
    ]

    subprocess.run(command, check=True)

    print(f"Created: {output_file}")


print("\n🔥 CAPTIONED VERTICAL CLIPS CREATED!")
print(f"Open: {OUTPUT_DIR}")