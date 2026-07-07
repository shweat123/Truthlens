# TruthLens

TruthLens is an explainable, offline news-credibility assistant built in Python.
It scores observable signals—sourcing, evidence language, clickbait, emotional
pressure, and attribution—without pretending that writing style proves truth.

## Run

Requires Python 3.10+ and no third-party packages:

On Windows, double-click `RUN_TRUTHLENS.bat` and keep its terminal window open.
Then visit `http://127.0.0.1:8000`.

Or run manually:

```powershell
python app.py
```

Open `http://127.0.0.1:8000`, click **Load demo**, then **Analyze credibility**.

## Test

```powershell
python -m unittest -v
```

## Presentation flow

1. Explain why binary “fake/real” labels are dangerous.
2. Load the sensational demo and inspect each warning signal.
3. Replace it with a sourced article containing links, named speakers, and data.
4. Compare the scores and explain that the tool supports—rather than replaces—verification.

## Attachments

The interface extracts text from PDF, DOCX, TXT, Markdown, and HTML files locally.
PNG/JPG/WEBP screenshots are transcribed locally in the browser with Tesseract.js,
loaded from jsDelivr. No account or API key is required. After extraction, the
credibility report runs automatically.

## AI fact-checking

TruthLens can use Gemini with Google Search grounding to verify general and
current claims and display sources. Keep your real API key private:

- For local use, store it in `.truthlens-settings.json`. This file is ignored by Git.
- For hosting/deployment, set `TRUTHLENS_GEMINI_API_KEY` as an environment variable.
- Use `.env.example` or `.truthlens-settings.example.json` only as templates.

Both current `AQ.` authentication keys and legacy `AIza` keys are accepted.
If Gemini is unavailable, the app clearly uses offline analysis.

## Publishing safely

Before pushing to GitHub, make sure these files are NOT uploaded:

- `.truthlens-settings.json`
- `.env`
- any screenshot or note containing your API key

This repo includes example placeholder files so other people can add their own key
without seeing yours.

## Architecture

The browser sends article text to a small Python HTTP server. `analyzer.py`
extracts transparent linguistic and sourcing signals, calculates bounded scores,
and returns a JSON report. The key limitation is deliberate: it does not claim
to verify real-world facts without external evidence.
