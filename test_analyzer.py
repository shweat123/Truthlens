import unittest
import base64

from analyzer import analyze_news
from extractor import extract_file


class AnalyzerTests(unittest.TestCase):
    def test_sourced_report_beats_sensational_post(self):
        sourced = analyze_news(
            "Agency publishes annual rainfall report",
            "According to the official report, rainfall increased 12 percent. "
            "Researchers said the analysis used data published in the journal. "
            "The full document is available at https://example.org/report.",
            "Example News",
        )
        sensational = analyze_news(
            "SHOCKING secret PROVES miracle cure!",
            "People are saying this unbelievable secret definitely cures everyone. "
            "Insiders claim it is guaranteed and you won't believe the result!",
            "",
        )
        self.assertGreater(sourced["score"], sensational["score"])
        self.assertGreater(sensational["signals"][2]["value"], sourced["signals"][2]["value"])

    def test_short_input_rejected(self):
        with self.assertRaises(ValueError):
            analyze_news("Too short", "Not enough.")

    def test_text_attachment_extraction(self):
        text = "This is a sufficiently long article with evidence and several useful details."
        result = extract_file("article.txt", "text/plain", base64.b64encode(text.encode()).decode())
        self.assertEqual(result["kind"], "Text document")
        self.assertIn("sufficiently long", result["text"])

    def test_conclusion_bands_and_claim_review(self):
        result = analyze_news(
            "SHOCKING secret claim proves everything",
            "People are saying this unbelievable secret definitely cures everyone. "
            "According to a report, researchers collected data from 100 participants.",
        )
        self.assertIn(result["conclusion"], {
            "Likely fake or unreliable", "Mixed signals", "Somewhat true", "Likely true news"
        })
        self.assertGreaterEqual(len(result["claim_review"]), 2)

    def test_unsupported_cola_medical_claim_scores_as_unreliable(self):
        result = analyze_news(
            "Coca Cola has never been better before",
            "Coca Cola has been announced as a cure for diabetes while diet coke "
            "is considered a medicine for children. Everyone should drink it once "
            "a day because one diet coke a day keeps the doctor away!",
            "Unknown viral post",
        )
        self.assertLess(result["truth_score"], 20)
        self.assertLess(result["score"], 50)
        self.assertEqual(result["conclusion"], "Likely fake or unreliable")


if __name__ == "__main__":
    unittest.main()
