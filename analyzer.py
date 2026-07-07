"""Explainable, offline news-credibility signal analysis."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import asdict, dataclass


SENSATIONAL = {
    "shocking", "bombshell", "unbelievable", "miracle", "secret", "exposed",
    "urgent", "breaking", "outrage", "disaster", "terrifying", "stunning",
    "destroy", "panic", "scandal", "hoax", "you won't believe", "must see",
}
ABSOLUTE = {
    "always", "never", "everyone", "nobody", "undeniable", "guaranteed",
    "proves", "definitely", "completely", "all", "none", "100%",
}
EVIDENCE = {
    "according to", "study", "research", "report", "data", "survey",
    "published", "journal", "official", "statement", "document", "analysis",
}
ATTRIBUTION = {
    "said", "told", "reported", "wrote", "confirmed",
    "spokesperson", "researchers", "officials", "experts",
}
VAGUE = {
    "sources say", "people are saying", "many believe", "they say",
    "insiders claim", "some say", "reportedly", "allegedly",
}
UNTRUSTED_SOURCE_WORDS = {"unknown", "viral", "social media", "whatsapp", "forwarded", "anonymous"}
EXTRAORDINARY_CLAIMS = {
    "cure diabetes": "Unsupported disease-cure claim",
    "cures diabetes": "Unsupported disease-cure claim",
    "cure cancer": "Unsupported cancer-cure claim",
    "cures cancer": "Unsupported cancer-cure claim",
    "cures every": "Universal cure claim",
    "cure every": "Universal cure claim",
    "miracle cure": "Miracle-treatment claim",
    "medicine for children": "Unsupported child-medicine claim",
    "safe for children": "Unsupported child-safety claim",
    "keeps doctor away": "Folk slogan presented as health advice",
    "doctors don't want": "Conspiracy-style medical claim",
    "100% safe": "Absolute safety claim",
    "guaranteed cure": "Guaranteed treatment claim",
}


@dataclass
class Signal:
    name: str
    value: int
    tone: str
    detail: str


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _hits(text: str, phrases: set[str]) -> list[str]:
    lower = text.lower()
    return sorted({p for p in phrases if re.search(rf"\b{re.escape(p)}\b", lower)})


def _review_claims(body: str) -> list[dict]:
    reviews = []
    for sentence in _sentences(body):
        words = re.findall(r"\b[\w'-]+\b", sentence)
        if len(words) < 6:
            continue
        good = len(_hits(sentence, EVIDENCE)) + len(_hits(sentence, ATTRIBUTION))
        risky = len(_hits(sentence, SENSATIONAL)) + len(_hits(sentence, ABSOLUTE))
        vague = len(_hits(sentence, VAGUE))
        has_checkable_detail = bool(re.search(r"\b\d+(?:\.\d+)?%?\b|https?://|www\.", sentence))
        if risky + vague >= 2:
            status = "High verification priority"
            tone = "bad"
            reason = "Uses strong, absolute, sensational, or vaguely attributed wording."
        elif good + int(has_checkable_detail) >= 2:
            status = "Has support signals"
            tone = "good"
            reason = "Includes attribution, evidence language, or a checkable detail."
        else:
            status = "Uncertain"
            tone = "warn"
            reason = "Not enough evidence is visible in the text to judge this claim."
        reviews.append({
            "statement": sentence[:280],
            "status": status,
            "tone": tone,
            "reason": reason,
        })
        if len(reviews) == 6:
            break
    return reviews


def analyze_news(title: str, body: str, source: str = "") -> dict:
    text = f"{title}. {body}".strip()
    words = re.findall(r"\b[\w'-]+\b", text)
    word_count = len(words)
    sentences = _sentences(text)

    if word_count < 8:
        raise ValueError("Please enter at least 8 words so the signals are meaningful.")

    sensational = _hits(text, SENSATIONAL)
    absolutes = _hits(text, ABSOLUTE)
    evidence = _hits(text, EVIDENCE)
    attribution = _hits(text, ATTRIBUTION)
    vague = _hits(text, VAGUE)
    extraordinary = [(phrase, label) for phrase, label in EXTRAORDINARY_CLAIMS.items()
                     if phrase in text.lower()]
    links = re.findall(r"https?://\S+|www\.\S+", text)
    numbers = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    quotes = re.findall(r'["“][^"”]{8,}["”]', text)
    caps_words = [w for w in words if len(w) > 3 and w.isupper()]
    exclamations = text.count("!")
    questions = text.count("?")

    score = 58
    score -= min(18, len(sensational) * 4)
    score -= min(12, len(absolutes) * 3)
    score -= min(10, len(vague) * 4)
    score -= min(10, len(caps_words) * 2 + exclamations * 2)
    score += min(14, len(evidence) * 3)
    score += min(10, len(attribution) * 2)
    score += min(8, len(numbers))
    score += min(6, len(quotes) * 2)
    score += min(6, len(links) * 3)
    source_lower = source.strip().lower()
    credible_source_supplied = bool(source_lower) and not any(
        word in source_lower for word in UNTRUSTED_SOURCE_WORDS
    )
    if credible_source_supplied:
        score += 3
    elif source_lower:
        score -= 8
    score -= min(28, len(extraordinary) * 12)
    if word_count < 35:
        score -= 8
    score = max(5, min(95, score))

    clickbait = min(
        100,
        10 + len(sensational) * 13 + len(absolutes) * 8
        + len(caps_words) * 7 + exclamations * 8 + questions * 4,
    )
    evidence_score = min(
        100,
        15 + len(evidence) * 12 + len(attribution) * 8
        + len(numbers) * 4 + len(quotes) * 8 + len(links) * 12,
    )
    transparency = min(100, max(5, 20 + credible_source_supplied * 25
                       - (bool(source_lower) and not credible_source_supplied) * 12
                       + len(links) * 18 + len(attribution) * 7))
    emotional = min(100, 8 + len(sensational) * 13 + len(caps_words) * 7 + exclamations * 8)

    truth_score = 52
    truth_score += min(16, len(evidence) * 3 + len(links) * 5 + len(numbers) * 2)
    truth_score += 6 if credible_source_supplied else 0
    truth_score -= min(55, len(extraordinary) * 22)
    truth_score -= min(20, len(absolutes) * 5 + len(vague) * 5)
    if extraordinary and not links:
        truth_score -= 15
    if not credible_source_supplied:
        truth_score -= 8
    truth_score = max(2, min(95, truth_score))

    overall_score = round(score * 0.48 + truth_score * 0.52)

    if overall_score > 85:
        conclusion, verdict_class = "Likely true news", "strong"
        conclusion_detail = "Very strong credibility signals, but confirm important claims with original sources."
    elif overall_score > 70:
        conclusion, verdict_class = "Somewhat true", "strong"
        conclusion_detail = "Mostly credible signals with some claims still needing independent verification."
    elif overall_score >= 50:
        conclusion, verdict_class = "Mixed signals", "mixed"
        conclusion_detail = "The article combines credible and risky signals. Review the statements below."
    else:
        conclusion, verdict_class = "Likely fake or unreliable", "risk"
        conclusion_detail = "High-risk writing or sourcing signals. Do not share before checking reliable sources."

    confidence = min(91, 42 + int(12 * math.log10(max(word_count, 10))) + min(word_count // 12, 25))
    if word_count < 35:
        confidence = min(confidence, 55)

    signals = [
        Signal("Evidence language", evidence_score, "good" if evidence_score >= 55 else "warn",
               f"{len(evidence)} evidence phrase(s), {len(numbers)} numeric detail(s), {len(links)} link(s)"),
        Signal("Source transparency", transparency, "good" if transparency >= 55 else "warn",
               ("Identifiable source supplied" if credible_source_supplied else
                "Unverifiable/unknown source" if source.strip() else "No publisher/source supplied")),
        Signal("Clickbait risk", clickbait, "bad" if clickbait >= 55 else "good",
               f"{len(sensational)} sensational phrase(s), {len(absolutes)} absolute claim(s)"),
        Signal("Emotional pressure", emotional, "bad" if emotional >= 55 else "good",
               f"{len(caps_words)} all-caps word(s), {exclamations} exclamation mark(s)"),
    ]

    flags = []
    if vague:
        flags.append(f"Vague attribution: {', '.join(vague[:3])}")
    if absolutes:
        flags.append(f"Absolute claims: {', '.join(absolutes[:4])}")
    if sensational:
        flags.append(f"Sensational wording: {', '.join(sensational[:4])}")
    if not links and not evidence:
        flags.append("No citations or evidence language detected")
    if not source.strip():
        flags.append("Publisher/source was not provided")
    elif not credible_source_supplied:
        flags.append("The supplied source is unknown or unverifiable")
    for _, label in extraordinary[:3]:
        flags.append(label)

    strengths = []
    if evidence:
        strengths.append(f"Evidence-oriented terms: {', '.join(evidence[:4])}")
    if attribution:
        strengths.append(f"Attribution language: {', '.join(attribution[:4])}")
    if numbers:
        strengths.append(f"Contains {len(numbers)} checkable numeric detail(s)")
    if quotes:
        strengths.append(f"Contains {len(quotes)} direct quotation(s)")

    common = Counter(w.lower() for w in words if len(w) >= 5)
    keywords = [w for w, _ in common.most_common(7)]

    return {
        "score": overall_score,
        "reliability_score": score,
        "truth_score": truth_score,
        "verdict": conclusion,
        "conclusion": conclusion,
        "conclusion_detail": conclusion_detail,
        "verdict_class": verdict_class,
        "confidence": confidence,
        "word_count": word_count,
        "signals": [asdict(s) for s in signals],
        "flags": flags[:5],
        "strengths": strengths[:5],
        "keywords": keywords,
        "claim_review": _review_claims(body),
        "questions": [
            "Who originally published this, and are they identifiable?",
            "Can the central claim be confirmed by two independent reliable sources?",
            "Does the article link to the study, document, or full quotation it references?",
        ],
        "disclaimer": (
            "This score evaluates writing and sourcing signals, not factual truth. "
            "Satire, breaking news, and well-written misinformation can fool text-only systems."
        ),
    }
