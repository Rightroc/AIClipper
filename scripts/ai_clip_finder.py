from pathlib import Path
import requests
import json
import re

TRANSCRIPT = Path("output/transcript.txt")
OUTPUT = Path("output/ai_clips.json")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"


# ============================================================
# 1. READ TRANSCRIPT
# ============================================================

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
        text = match.group(3).strip()

        segments.append({
            "start": start,
            "end": end,
            "text": text
        })


# ============================================================
# 2. CREATE 25–60 SECOND CANDIDATES
# ============================================================

candidates = []

for i in range(len(segments)):

    start = segments[i]["start"]

    text_parts = []

    for j in range(i, len(segments)):

        text_parts.append(segments[j]["text"])

        end = segments[j]["end"]

        duration = end - start

        if duration < 25:
            continue

        if duration > 60:
            break

        candidates.append({
            "start": start,
            "end": end,
            "duration": round(duration, 2),
            "text": " ".join(text_parts)
        })


print(f"Generated {len(candidates)} candidates.")


# ============================================================
# 3. SCORE CANDIDATES
# ============================================================

interesting_words = [

    "deadliest",
    "danger",
    "dangerous",
    "kill",
    "death",

    "money",
    "hundred",
    "thousand",

    "win",
    "lose",
    "winning",

    "mom",
    "mother",

    "crazy",
    "important",
    "problem",
    "secret",

    "never",
    "always",
    "why",
    "how",

    "amazon",
    "jaguar",
    "snake",
    "anaconda",

    "race",
    "challenge",
    "destroyed",

    "fight",
    "survive",
    "survival",

    "shock",
    "scary",
    "danger"
]


for candidate in candidates:

    text = candidate["text"].lower()

    score = 0

    for word in interesting_words:

        if word in text:
            score += 1

    # Prefer 30–50 second clips
    if 30 <= candidate["duration"] <= 50:
        score += 3

    candidate["score"] = score


# ============================================================
# 4. SORT BY SCORE
# ============================================================

candidates.sort(
    key=lambda x: x["score"],
    reverse=True
)


# ============================================================
# 5. BUILD A DIVERSE CANDIDATE POOL
# ============================================================

# We want enough candidates for Qwen to choose from.
# But we don't want 10 versions of the same moment.

diverse_candidates = []

for candidate in candidates:

    too_similar = False

    for selected in diverse_candidates:

        overlap_start = max(
            candidate["start"],
            selected["start"]
        )

        overlap_end = min(
            candidate["end"],
            selected["end"]
        )

        overlap = max(
            0,
            overlap_end - overlap_start
        )

        smaller_duration = min(
            candidate["duration"],
            selected["duration"]
        )

        if smaller_duration > 0:

            overlap_ratio = overlap / smaller_duration

            if overlap_ratio > 0.60:

                too_similar = True
                break

    if not too_similar:

        diverse_candidates.append(candidate)

    if len(diverse_candidates) >= 10:
        break


candidates = diverse_candidates


# ============================================================
# 6. GIVE CANDIDATES IDs
# ============================================================

for index, candidate in enumerate(candidates, start=1):

    candidate["id"] = index


print("\nDIVERSE CANDIDATES:\n")

for candidate in candidates:

    print(
        f"{candidate['id']}. "
        f"{candidate['start']}s → "
        f"{candidate['end']}s "
        f"({candidate['duration']}s)"
    )


# ============================================================
# 7. SEND CANDIDATES TO QWEN
# ============================================================

candidate_text = ""

for candidate in candidates:

    candidate_text += f"""

CANDIDATE {candidate['id']}

START: {candidate['start']}
END: {candidate['end']}
DURATION: {candidate['duration']} seconds

TEXT:
{candidate['text']}

"""


prompt = f"""
You are an expert short-form video editor.

Choose the 3 BEST video clips from the candidates below.

The clips will be used for:

TikTok
Instagram Reels
YouTube Shorts

Choose clips that:

- have a strong opening
- are interesting
- create curiosity
- contain emotion, tension, surprise or useful information
- make sense as standalone clips
- are different moments from the video

IMPORTANT RULES:

1. Choose ONLY candidate IDs that actually exist.
2. Choose exactly 3 candidates.
3. Do NOT create timestamps.
4. Do NOT summarize.
5. Do NOT explain your choices.

Your entire response MUST be exactly three candidate numbers separated by commas.

Example:

1, 4, 7

AVAILABLE CANDIDATES:
{candidate_text}
"""


print("\nAsking Qwen to choose the best candidates...")


response = requests.post(

    OLLAMA_URL,

    json={
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0
        }
    },

    timeout=300
)


response.raise_for_status()

result = response.json()

ai_response = result["response"].strip()


print("\nQWEN RESPONSE:")

print(ai_response)


# ============================================================
# 8. EXTRACT VALID IDs
# ============================================================

numbers = re.findall(
    r"\b\d+\b",
    ai_response
)

valid_ids = {
    candidate["id"]
    for candidate in candidates
}

selected_ids = []


for number in numbers:

    number = int(number)

    if number in valid_ids:

        if number not in selected_ids:

            selected_ids.append(number)

    if len(selected_ids) == 3:

        break


# ============================================================
# 9. FALLBACK IF QWEN DOES NOT RETURN 3 VALID CLIPS
# ============================================================

if len(selected_ids) < 3:

    print("\nQwen did not return 3 valid candidates.")
    print("Activating automatic fallback...")

    # The candidate pool has already been filtered
    # for diversity, so simply use the remaining
    # highest-ranked candidates.

    for candidate in candidates:

        candidate_id = candidate["id"]

        if candidate_id not in selected_ids:

            selected_ids.append(candidate_id)

        if len(selected_ids) == 3:

            break


print("\nSELECTED CANDIDATE IDs:")

print(selected_ids)

# ============================================================
# 10. CREATE FINAL CLIPS
# ============================================================

final_clips = []


for candidate_id in selected_ids:

    for candidate in candidates:

        if candidate["id"] == candidate_id:

            final_clips.append({

                "start": candidate["start"],

                "end": candidate["end"],

                "duration": candidate["duration"],

                "reason": "Selected by local AI",

                "hook": candidate["text"][:150]

            })


# ============================================================
# 11. FINAL SAFETY CHECK
# ============================================================

if len(final_clips) < 3:

    print(
        "\nERROR: Could not find 3 distinct clips."
    )

else:

    print("\nFINAL CLIPS:\n")

    for index, clip in enumerate(
        final_clips,
        start=1
    ):

        print(
            f"Clip {index}: "
            f"{clip['start']}s → "
            f"{clip['end']}s "
            f"({clip['duration']}s)"
        )


# ============================================================
# 12. SAVE JSON
# ============================================================

OUTPUT.write_text(

    json.dumps(
        {
            "clips": final_clips
        },
        indent=2
    ),

    encoding="utf-8"
)


print("\nSaved to:")

print(OUTPUT)