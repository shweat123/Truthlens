# TruthLens Backend — Presentation Walkthrough

## 1. Request enters the Python server

Open `app.py`.

- `ThreadingHTTPServer` runs the local website.
- `POST /api/analyze` receives the headline, article, and publisher.
- The offline analyzer always creates a fallback report.
- When a Gemini key is configured, the server runs the grounded AI fact-check.
- The backend returns one JSON response to the interface.

## 2. AI verifies claims using current information

Open `ai_analyzer.py`.

- The prompt asks Gemini to separate facts, opinions, predictions, and satire.
- `google_search` enables live web grounding.
- Gemini returns reliability and truth scores separately.
- It also returns a verdict and a statement-by-statement explanation.
- Grounding metadata supplies the sources checked.

## 3. Offline fallback remains available

Open `analyzer.py`.

- Detects evidence, attribution, clickbait, emotional pressure, and vague sourcing.
- Penalizes unknown viral sources and unsupported extraordinary claims.
- Produces a transparent result if the AI or internet is unavailable.

## 4. Attachments become readable text

Open `extractor.py`.

- Extracts text from PDF, DOCX, TXT, Markdown, and HTML.
- Screenshots are read in the browser using local OCR.
- Extracted text is passed into the same analysis pipeline.

## One-line architecture

`Article / attachment → text extraction → offline signals → Gemini + Google Search → JSON report → dashboard`

## Strong closing line

> TruthLens does not label news from wording alone. It separates source reliability
> from factual truth, checks individual claims using current web evidence, and keeps
> an explainable offline fallback.
