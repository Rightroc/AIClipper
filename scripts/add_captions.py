from pathlib import Path
import subprocess
import re

INPUT_DIR = Path("output/ai_generated")
SRT_FILE = Path("output/subtitles.srt")
OUTPUT_DIR = Path("output/final")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def time_to_seconds(timestamp):
    h, m, s = timestamp.replace(",", ".").split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def seconds_to_srt(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))

    if millis >= 1000:
        secs += 1
        millis = 0

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# Read original subtitles
content = SRT_FILE.read_text(encoding="utf-8")

blocks = re.split(r"\n\s*\n", content.strip())

subtitles = []

for block in blocks:

    lines = block.splitlines()

    if len(lines) < 3:
        continue

    timing = lines[1]

    match = re.match(
        r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})",
        timing
    )

    if not match:
        continue

    start = time_to_seconds(match.group(1))
    end = time_to_seconds(match.group(2))
    text = "\n".join(lines[2:])

    subtitles.append({
        "start": start,
        "end": end,
        "text": text
    })


# Read AI clip timestamps
import json

ai_data = json.loads(
    Path("output/ai_clips.json").read_text(
        encoding="utf-8"
    )
)

clips = ai_data["clips"]


for index, clip in enumerate(clips, start=1):

    clip_start = clip["start"]
    clip_end = clip["end"]

    print(
        f"\nAdding captions to Clip {index}: "
        f"{clip_start}s → {clip_end}s"
    )

    clip_subtitles = []

    subtitle_number = 1

    for subtitle in subtitles:

        # Subtitle must overlap the selected clip
        if subtitle["end"] <= clip_start:
            continue

        if subtitle["start"] >= clip_end:
            continue

        new_start = max(
            subtitle["start"],
            clip_start
        ) - clip_start

        new_end = min(
            subtitle["end"],
            clip_end
        ) - clip_start

        if new_end <= 0:
            continue

        clip_subtitles.append(
            f"{subtitle_number}\n"
            f"{seconds_to_srt(new_start)} --> "
            f"{seconds_to_srt(new_end)}\n"
            f"{subtitle['text']}\n"
        )

        subtitle_number += 1


    # Create SRT for this clip
    srt_path = OUTPUT_DIR / f"clip_{index:02d}.srt"

    srt_path.write_text(
        "\n".join(clip_subtitles),
        encoding="utf-8"
    )


    input_video = (
        INPUT_DIR /
        f"clip_{index:02d}.mp4"
    )

    output_video = (
        OUTPUT_DIR /
        f"clip_{index:02d}.mp4"
    )


    # Caption style
    subtitle_filter = (
        f"subtitles={srt_path.as_posix()}:"
        "force_style="
        "'FontName=Arial,"
        "FontSize=12,"
        "Bold=1,"
        "PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=220'"
    )


    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_video),
        "-vf",
        subtitle_filter,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "copy",
        str(output_video)
    ]


    subprocess.run(
        command,
        check=True
    )


    print(
        f"Saved: {output_video}"
    )


print("\nDone! 🎉")
print(
    f"Captioned clips saved in: {OUTPUT_DIR}"
)