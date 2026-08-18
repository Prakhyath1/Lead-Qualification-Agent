import unittest
from src.models import LeadEvaluation, FitBreakdown, IntentBreakdown, LeadInput
from src.config import HOT_THRESHOLD, WARM_THRESHOLD


class TestLeadModels(unittest.TestCase):
    def test_lead_evaluation_valid(self):
        eval_data = {
            "fit_score": 45,
            "intent_score": 48,
            "total_score": 93,
            "tier": "HOT",
            "fit_breakdown": {
                "company_size_score": 15,
                "seniority_score": 18,
                "industry_fit_score": 12,
                "fit_summary": "Strong enterprise fit",
            },
            "intent_breakdown": {
                "behavior_signal_score": 24,
                "urgency_timeline_score": 15,
                "budget_readiness_score": 9,
                "intent_summary": "High urgency and approved budget",
            },
            "key_positive_signals": ["Requested live demo", "Approved $80k budget"],
            "red_flags": [],
            "rationale": "High fit executive with immediate deployment need.",
            "next_action": "Schedule immediate discovery call with Account Executive.",
            "sla_response_time": "Immediate (<1 hour)",
        }
        model = LeadEvaluation(**eval_data)
        self.assertEqual(model.total_score, 93)
        self.assertEqual(model.tier, "HOT")
        self.assertEqual(model.fit_score, 45)
        self.assertEqual(model.intent_score, 48)

    def test_tier_thresholds(self):
        self.assertEqual(HOT_THRESHOLD, 80)
        self.assertEqual(WARM_THRESHOLD, 50)

    def test_lead_input_defaults(self):
        lead = LeadInput(name="Test User", company="Test Corp")
        self.assertEqual(lead.name, "Test User")
        self.assertEqual(lead.company, "Test Corp")
        self.assertEqual(lead.company_size, "Unknown")
        self.assertEqual(lead.budget_status, "Unknown")

    def test_tier_normalization(self):
        eval_data = {
            "fit_score": 10,
            "intent_score": 10,
            "total_score": 20,
            "tier": "cold",  # lowercase should be normalized to uppercase COLD
            "rationale": "Poor fit",
            "next_action": "Drip campaign",
        }
        model = LeadEvaluation(**eval_data)
        self.assertEqual(model.tier, "COLD")


if __name__ == "__main__":
    unittest.main()
