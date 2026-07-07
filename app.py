"""TruthLens: dependency-free Python web application."""

from __future__ import annotations

import json
import mimetypes
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from analyzer import analyze_news
from ai_analyzer import analyze_with_ai, validate_key
from extractor import extract_file


ROOT = Path(__file__).parent
STATIC = ROOT / "static"
SETTINGS = ROOT / ".truthlens-settings.json"


def load_key() -> str:
    env_key = os.getenv("TRUTHLENS_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    if env_key:
        return env_key.strip()
    try:
        return str(json.loads(SETTINGS.read_text(encoding="utf-8")).get("gemini_api_key", "")).strip()
    except (OSError, json.JSONDecodeError):
        return ""


class Handler(BaseHTTPRequestHandler):
    def _json(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        if self.path not in {"/api/analyze", "/api/extract", "/api/settings"}:
            self._json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 18_000_000:
                raise ValueError("Request is too large.")
            data = json.loads(self.rfile.read(length))
            if self.path == "/api/settings":
                key = str(data.get("gemini_api_key", "")).strip()
                if not key:
                    raise ValueError("Please enter a Gemini API key.")
                validate_key(key)
                SETTINGS.write_text(json.dumps({"gemini_api_key": key}), encoding="utf-8")
                result = {"configured": True}
            elif self.path == "/api/extract":
                result = extract_file(
                    str(data.get("filename", "")),
                    str(data.get("mime", "")),
                    str(data.get("data", "")),
                )
            else:
                result = analyze_news(
                    str(data.get("title", "")),
                    str(data.get("body", "")),
                    str(data.get("source", "")),
                )
                key = load_key()
                if key:
                    try:
                        result.update(analyze_with_ai(
                            str(data.get("title", "")),
                            str(data.get("body", "")),
                            str(data.get("source", "")),
                            key,
                        ))
                        result["score"] = round(result["reliability_score"] * .4 + result["truth_score"] * .6)
                        result["analysis_mode"] = "AI + Google Search"
                    except ValueError as exc:
                        result["analysis_mode"] = "Offline fallback"
                        result["ai_error"] = str(exc)
                else:
                    result["analysis_mode"] = "Offline fallback"
                    result["ai_error"] = "AI fact-checking is not configured."
            self._json(result)
        except (ValueError, json.JSONDecodeError) as exc:
            self._json({"error": str(exc)}, 400)
        except Exception:
            self._json({"error": "Analysis failed unexpectedly."}, 500)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/settings":
            self._json({"configured": bool(load_key())})
            return
        relative = "index.html" if path == "/" else path.lstrip("/")
        file = (STATIC / relative).resolve()
        if STATIC.resolve() not in file.parents or not file.is_file():
            self.send_error(404)
            return
        content = file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[TruthLens] {fmt % args}")


if __name__ == "__main__":
    address = ("127.0.0.1", 8000)
    print("TruthLens is running at http://127.0.0.1:8000")
    ThreadingHTTPServer(address, Handler).serve_forever()
