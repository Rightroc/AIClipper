from pathlib import Path
import subprocess
import os
import sys


PROJECT_DIR = Path(__file__).resolve().parent.parent

VIDEO = Path(
    os.environ.get(
        "AICLIPPER_INPUT",
        str(PROJECT_DIR / "input" / "current.mp4")
    )
)

OUTPUT_DIR = PROJECT_DIR / "output"
OUTPUT_TEXT = OUTPUT_DIR / "transcript.txt"
OUTPUT_SRT = OUTPUT_DIR / "subtitles.srt"

MODEL = PROJECT_DIR / "models" / "ggml-base.en.bin"

OUTPUT_DIR.mkdir(exist_ok=True)


if not VIDEO.exists():
    print(f"❌ Video not found: {VIDEO}")
    sys.exit(1)

if not MODEL.exists():
    print(f"❌ Whisper model not found: {MODEL}")
    sys.exit(1)


print("\n🎙️ Transcribing with FFmpeg Whisper...")
print(f"Video: {VIDEO}")
print(f"Model: {MODEL}")


# Use project-relative paths so FFmpeg does not
# misinterpret the Windows C: drive as a filter separator.
model_path = "./models/ggml-base.en.bin"
srt_path = "./output/subtitles.srt"


whisper_filter = (
    f"whisper="
    f"model={model_path}:"
    f"language=en:"
    f"destination={srt_path}:"
    f"format=srt"
)


ffmpeg_command = [
    "ffmpeg",
    "-y",
    "-i",
    str(VIDEO),
    "-vn",
    "-af",
    whisper_filter,
    "-f",
    "null",
    "-"
]


result = subprocess.run(ffmpeg_command)


if result.returncode != 0:
    print("\n❌ FFmpeg Whisper transcription failed.")
    sys.exit(result.returncode)


if not OUTPUT_SRT.exists():
    print("\n❌ Whisper finished but no SRT file was created.")
    sys.exit(1)


print("\n✅ Whisper transcription complete!")
print(f"Subtitles: {OUTPUT_SRT}")


def srt_to_seconds(timestamp):
    timestamp = timestamp.replace(",", ".")
    hours, minutes, seconds = timestamp.split(":")

    return (
        int(hours) * 3600
        + int(minutes) * 60
        + float(seconds)
    )


with open(
    OUTPUT_SRT,
    "r",
    encoding="utf-8"
) as srt_file:

    lines = srt_file.readlines()


transcript_lines = []

i = 0

while i < len(lines):

    line = lines[i].strip()

    if line.isdigit():

        i += 1

        if i >= len(lines):
            break

        timing = lines[i].strip()

        if "-->" not in timing:
            i += 1
            continue

        start_time, end_time = [
            x.strip()
            for x in timing.split("-->")
        ]

        start = srt_to_seconds(start_time)
        end = srt_to_seconds(end_time)

        i += 1

        text_parts = []

        while i < len(lines) and lines[i].strip():
            text_parts.append(lines[i].strip())
            i += 1

        text = " ".join(text_parts)

        if text:
            transcript_lines.append(
                f"[{start:.2f} --> {end:.2f}] {text}"
            )

    i += 1


with open(
    OUTPUT_TEXT,
    "w",
    encoding="utf-8"
) as text_file:

    for line in transcript_lines:
        text_file.write(line + "\n")


print(f"Transcript: {OUTPUT_TEXT}")
print(f"Segments: {len(transcript_lines)}")