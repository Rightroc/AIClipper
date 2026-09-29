from faster_whisper import WhisperModel
from pathlib import Path

VIDEO = Path("input/test.mp4")
OUTPUT_TEXT = Path("output/transcript.txt")
OUTPUT_SRT = Path("output/subtitles.srt")

print("Loading Whisper...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Transcribing video...")

segments, info = model.transcribe(
    str(VIDEO),
    beam_size=5
)


def srt_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


with open(OUTPUT_TEXT, "w", encoding="utf-8") as text_file, \
     open(OUTPUT_SRT, "w", encoding="utf-8") as srt_file:

    for index, segment in enumerate(segments, start=1):

        start = segment.start
        end = segment.end
        text = segment.text.strip()

        # Normal transcript
        text_file.write(
            f"[{start:.2f} --> {end:.2f}] {text}\n"
        )

        # SRT subtitle
        srt_file.write(f"{index}\n")
        srt_file.write(
            f"{srt_time(start)} --> {srt_time(end)}\n"
        )
        srt_file.write(f"{text}\n\n")


print("\nTranscription complete!")
print(f"Transcript: {OUTPUT_TEXT}")
print(f"Subtitles:  {OUTPUT_SRT}")