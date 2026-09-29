from pathlib import Path
import re

TRANSCRIPT = Path("output/transcript.txt")
CLIP_DIR = Path("output/clips")
CLIP_DIR.mkdir(parents=True, exist_ok=True)

# Words/phrases that often indicate interesting short-form moments
HOOK_WORDS = [
    "deadliest",
    "million",
    "thousand",
    "hundred",
    "money",
    "win",
    "lost",
    "danger",
    "kill",
    "death",
    "secret",
    "mistake",
    "never",
    "always",
    "best",
    "worst",
    "crazy",
    "important",
    "problem",
    "why",
    "how",
    "because",
    "mom",
]

def parse_timestamp(timestamp):
    minutes, seconds = timestamp.split(":")
    return int(minutes) * 60 + float(seconds)


def timestamp_to_seconds(value):
    minutes, seconds = value.split(":")
    return int(minutes) * 60 + float(seconds)


# Read transcript
lines = TRANSCRIPT.read_text(encoding="utf-8").splitlines()

segments = []

for line in lines:
    match = re.match(
        r"\[(\d+\.\d+) --> (\d+\.\d+)\]\s*(.*)",
        line
    )

    if match:
        start = float(match.group(1))
        end = float(match.group(2))
        text = match.group(3)

        segments.append({
            "start": start,
            "end": end,
            "text": text
        })


# Build candidate clips
candidates = []

for i in range(len(segments)):
    start = segments[i]["start"]

    text_parts = []
    end = start

    # Create windows of roughly 20–60 seconds
    for j in range(i, min(i + 12, len(segments))):

        text_parts.append(segments[j]["text"])
        end = segments[j]["end"]

        duration = end - start

        if duration < 20:
            continue

        if duration > 60:
            break

        text = " ".join(text_parts).lower()

        score = 0

        # Hook words
        for word in HOOK_WORDS:
            if word in text:
                score += 2

        # Numbers
        if re.search(r"\d+", text):
            score += 2

        # Questions
        if "?" in text:
            score += 2

        # Emotional language
        emotional_words = [
            "love",
            "hate",
            "afraid",
            "scared",
            "excited",
            "angry",
            "mom",
            "family",
            "win",
            "lose",
        ]

        for word in emotional_words:
            if word in text:
                score += 2

        # Prefer clips around 30–50 seconds
        if 30 <= duration <= 50:
            score += 3

        candidates.append({
            "start": start,
            "end": end,
            "duration": duration,
            "score": score,
            "text": " ".join(text_parts)
        })


# Sort highest scoring clips first
candidates.sort(key=lambda x: x["score"], reverse=True)


# Remove clips that overlap heavily
selected = []

for candidate in candidates:

    overlaps = False

    for existing in selected:

        overlap_start = max(candidate["start"], existing["start"])
        overlap_end = min(candidate["end"], existing["end"])

        if overlap_end > overlap_start:
            overlap = overlap_end - overlap_start
            candidate_duration = candidate["duration"]

            if overlap / candidate_duration > 0.5:
                overlaps = True
                break

    if not overlaps:
        selected.append(candidate)

    if len(selected) == 5:
        break


print("\nTOP CLIP CANDIDATES\n")

for number, clip in enumerate(selected, start=1):

    print(
        f"Clip {number}: "
        f"{clip['start']:.2f}s → {clip['end']:.2f}s "
        f"({clip['duration']:.1f}s)"
    )

    print(f"Score: {clip['score']}")
    print(f"Text: {clip['text'][:300]}...")
    print("-" * 70)


# Save timestamps
with open("output/clips.txt", "w", encoding="utf-8") as f:

    for number, clip in enumerate(selected, start=1):

        f.write(
            f"{number}|"
            f"{clip['start']:.2f}|"
            f"{clip['end']:.2f}\n"
        )

print("\nSaved clip timestamps to output/clips.txt")