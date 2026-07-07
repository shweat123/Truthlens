"""Gemini with Google Search grounded fact-checking."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request


def validate_key(api_key: str) -> None:
    """Validate by calling Gemini, never by guessing the credential's prefix."""
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps({
            "contents": [{"parts": [{"text": "Reply with only OK."}]}],
            "generationConfig": {"maxOutputTokens": 4, "temperature": 0},
        }).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise ValueError("Gemini rejected this credential.")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="ignore")
        try:
            message = json.loads(detail)["error"]["message"]
        except Exception:
            message = f"Google returned HTTP {exc.code}"
        raise ValueError(f"Gemini rejected this key: {message}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("Could not reach Gemini to validate the key.") from exc


def analyze_with_ai(title: str, body: str, source: str, api_key: str) -> dict:
    prompt = f"""Act as a rigorous news fact-checker. Use Google Search to verify
each major factual claim against current reputable sources. Do not infer truth
from writing style. Return ONLY JSON:
{{
"reliability_score": 0-100 integer,
"truth_score": 0-100 integer,
"conclusion": one of ["Likely fake or unreliable","Mixed signals","Somewhat true","Likely true news"],
"conclusion_detail": "direct plain-language answer explaining what is true or false",
"claim_review": [{{"statement":"claim","status":"True|Mostly true|Misleading|False|Unverified|Opinion","tone":"good|warn|bad","reason":"evidence-based explanation"}}]
}}
Reliability measures sourcing; truth measures factual correctness. Fabricated or
unsupported claims score below 50 even when calmly written. Review at most 6 claims.
HEADLINE: {title}
ARTICLE: {body[:40000]}
CLAIMED SOURCE: {source or "not supplied"}"""
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.1},
        }).encode(),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            raw = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="ignore")
        try:
            message = json.loads(detail)["error"]["message"]
        except Exception:
            message = f"Google returned HTTP {exc.code}"
        raise ValueError(message) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ValueError("Could not reach Gemini. Check the internet connection.") from exc

    try:
        candidate = raw["candidates"][0]
        text = "".join(p.get("text", "") for p in candidate["content"]["parts"])
        match = re.search(r"\{.*\}", re.sub(r"```(?:json)?|```", "", text), re.S)
        result = json.loads(match.group()) if match else {}
        metadata = candidate.get("groundingMetadata", {})
        result["sources"] = [
            {"title": c["web"]["title"], "url": c["web"]["uri"]}
            for c in metadata.get("groundingChunks", [])
            if c.get("web", {}).get("title") and c.get("web", {}).get("uri")
        ][:8]
        return result
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("Gemini returned an incomplete fact-check.") from exc
