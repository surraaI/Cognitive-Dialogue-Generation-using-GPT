from __future__ import annotations

import re

from app.cognitive.types import AttentionSignals


_STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "but",
    "to",
    "of",
    "in",
    "on",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "be",
    "as",
    "at",
    "by",
    "it",
    "this",
    "that",
    "these",
    "those",
    "i",
    "you",
    "we",
    "they",
    "he",
    "she",
    "them",
    "my",
    "your",
    "our",
}


def extract_attention(text: str) -> AttentionSignals:
    """
    Lightweight backend attention signal extractor.
    - Entities: naive detection of TitleCase tokens / acronyms.
    - Keyphrases: top multi-word chunks from simple token windows.
    - Intent: detection of question type (what, why, how, explain, define)
    - Ambiguity: heuristic based on vague pronouns + short length.
    """
    raw = text.strip()
    tokens = re.findall(r"[A-Za-z0-9_\-]+", raw)
    lower = [t.lower() for t in tokens]

    # Naive entities: acronyms or TitleCase words.
    entities = []
    seen = set()
    for t in tokens:
        if (len(t) >= 2 and t.isupper()) or (t[:1].isupper() and t[1:].islower()):
            k = t
            if k.lower() not in seen:
                seen.add(k.lower())
                entities.append({"text": k, "score": 0.7})

    # Keyphrases: 2-3 word windows excluding stopwords.
    keyphrases: dict[str, float] = {}
    for n in (2, 3):
        for i in range(0, max(0, len(lower) - n + 1)):
            window = lower[i : i + n]
            if any(w in _STOPWORDS for w in window):
                continue
            phrase = " ".join(window)
            # Prefer longer phrases slightly.
            keyphrases[phrase] = keyphrases.get(phrase, 0.0) + (1.0 + 0.1 * (n - 2))

    top_phrases = sorted(keyphrases.items(), key=lambda kv: kv[1], reverse=True)[:10]
    keyphrase_list = [{"text": p, "score": float(s)} for p, s in top_phrases]

    # Intent detection: identify question type
    intent = None
    intent_patterns = {
        "clarify": r"(what|which|who|when|where|how)[\s\?]",
        "explain": r"(explain|what is|describe|tell|define)",
        "why": r"(why|reason|cause|because)",
        "confirm": r"(right|correct|is that|am i)",
    }
    raw_lower = raw.lower()
    for intent_type, pattern in intent_patterns.items():
        if re.search(pattern, raw_lower):
            intent = intent_type
            break

    vague_markers = {"it", "that", "this", "something", "stuff", "things"}
    vagueness = sum(1 for w in lower if w in vague_markers)
    brevity = 1.0 if len(lower) < 6 else 0.0
    ambiguity_score = min(1.0, 0.15 * vagueness + 0.25 * brevity)

    return AttentionSignals(
        entities=entities,
        keyphrases=keyphrase_list,
        intent=intent,
        ambiguity_score=float(ambiguity_score),
    )

