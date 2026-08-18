import unittest
import tempfile
import json
from pathlib import Path
from src.utils import load_leads_from_file, export_to_json, export_to_csv, generate_markdown_report


class TestDataUtils(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_json_load_and_export(self):
        sample_data = [
            {
                "id": "L-TEST-001",
                "name": "Jane Doe",
                "company": "Acme Inc.",
                "total_score": 90,
                "tier": "HOT",
                "fit_score": 45,
                "intent_score": 45,
                "next_action": "Call today",
                "rationale": "High intent",
                "evaluation": {
                    "fit_score": 45,
                    "intent_score": 45,
                    "total_score": 90,
                    "tier": "HOT",
                    "sla_response_time": "1 hour",
                    "next_action": "Call today",
                    "rationale": "High intent",
                    "key_positive_signals": ["Demo request"],
                    "red_flags": [],
                },
            }
        ]

        json_file = self.temp_path / "test_leads.json"
        export_to_json(sample_data, json_file)
        self.assertTrue(json_file.exists())

        loaded = load_leads_from_file(json_file)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "Jane Doe")

    def test_csv_export(self):
        sample_data = [
            {
                "id": "L-TEST-002",
                "name": "John Smith",
                "company": "Beta Corp",
                "total_score": 60,
                "tier": "WARM",
                "fit_score": 35,
                "intent_score": 25,
                "next_action": "Send case study",
                "rationale": "Mid-tier fit",
                "evaluation": {
                    "fit_score": 35,
                    "intent_score": 25,
                    "total_score": 60,
                    "tier": "WARM",
                    "sla_response_time": "24 hours",
                    "next_action": "Send case study",
                    "rationale": "Mid-tier fit",
                    "key_positive_signals": ["Webinar attendee"],
                    "red_flags": [],
                },
            }
        ]
        csv_file = self.temp_path / "test_leads.csv"
        export_to_csv(sample_data, csv_file)
        self.assertTrue(csv_file.exists())

        loaded = load_leads_from_file(csv_file)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["name"], "John Smith")

    def test_markdown_report_generation(self):
        sample_data = [
            {
                "id": "L-TEST-003",
                "name": "Alice Wonderland",
                "company": "Wonder Corp",
                "job_title": "CTO",
                "industry": "Software",
                "total_score": 95,
                "tier": "HOT",
                "fit_score": 50,
                "intent_score": 45,
                "next_action": "Immediate Discovery Call",
                "rationale": "Top tier prospect",
                "evaluation": {
                    "sla_response_time": "Immediate (<1 hour)",
                    "key_positive_signals": ["Enterprise RFP"],
                    "red_flags": [],
                },
            }
        ]
        report_file = self.temp_path / "report.md"
        generate_markdown_report(sample_data, report_file)
        self.assertTrue(report_file.exists())
        content = report_file.read_text(encoding="utf-8")
        self.assertIn("Alice Wonderland", content)
        self.assertIn("HOT", content)


if __name__ == "__main__":
    unittest.main()
