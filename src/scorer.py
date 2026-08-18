import json
import time
from typing import Dict, Any, Optional, List
from groq import Groq
from src.models import LeadEvaluation, FitBreakdown, IntentBreakdown
from src.config import (
    PRIMARY_MODEL,
    FALLBACK_MODELS,
    HOT_THRESHOLD,
    WARM_THRESHOLD,
    SCORING_LOGIC_FILE,
)
from src.utils import safe_print


class LeadScorer:
    def __init__(self, api_key: str, model_name: str = PRIMARY_MODEL):
        self.api_key = api_key
        self.primary_model = model_name
        self.client = Groq(api_key=api_key)
        self.scoring_rubric = self._load_scoring_rubric()

    def _load_scoring_rubric(self) -> str:
        """Loads the scoring logic documentation from SCORING_LOGIC.md."""
        try:
            if SCORING_LOGIC_FILE.exists():
                with open(SCORING_LOGIC_FILE, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception:
            pass
        return "Score out of 100 based on B2B SaaS Ideal Customer Profile (Fit up to 50, Intent up to 50)."

    def evaluate_lead(self, lead_dict: Dict[str, Any], max_retries: int = 3) -> Optional[LeadEvaluation]:
        """
        Evaluates a single lead against the scoring rubric using Groq LLM with fallback models
        and exponential backoff retry logic.
        """
        prompt = f"""
You are an expert Chief Revenue Officer and Sales Operations AI Agent qualifying inbound B2B sales leads.

### SCORING RUBRIC & METHODOLOGY:
{self.scoring_rubric}

### LEAD TO EVALUATE:
{json.dumps(lead_dict, indent=2, ensure_ascii=False)}

### INSTRUCTIONS:
1. Carefully analyze the lead across two 50-point pillars:
   - **Fit (0-50 pts)**: Company Size (0-15), Seniority & Authority (0-20), Industry / Domain Fit (0-15).
   - **Intent (0-50 pts)**: Behavioral Signals (0-25), Timeline Urgency (0-15), Budget Readiness (0-10).
2. Check for Red Flags & Disqualifiers (students, personal email on enterprise apps, competitor intelligence scouts, non-business inquiries).
3. Compute the sub-scores and ensure `fit_score` is the sum of fit sub-scores, and `intent_score` is the sum of intent sub-scores.
4. Total score MUST equal `fit_score + intent_score` (0-100).
5. Assign Tier:
   - **HOT**: 80 - 100 (Immediate Account Executive discovery call)
   - **WARM**: 50 - 79 (SDR qualification & targeted case study nurture)
   - **COLD**: 0 - 49 (Automated marketing drip or disqualified)
6. Define a concrete, actionable `next_action` and realistic `sla_response_time` (<1 hour, <24 hours, 7-day drip).

Respond strictly in valid JSON matching this schema:
{{
  "fit_score": 0-50,
  "intent_score": 0-50,
  "total_score": 0-100,
  "tier": "HOT" | "WARM" | "COLD",
  "fit_breakdown": {{
    "company_size_score": 0-15,
    "seniority_score": 0-20,
    "industry_fit_score": 0-15,
    "fit_summary": "Explanation of fit attributes"
  }},
  "intent_breakdown": {{
    "behavior_signal_score": 0-25,
    "urgency_timeline_score": 0-15,
    "budget_readiness_score": 0-10,
    "intent_summary": "Explanation of intent signals"
  }},
  "key_positive_signals": ["Signal 1", "Signal 2"],
  "red_flags": ["Risk/disqualifier if any"],
  "rationale": "Comprehensive explanation of why this score and tier were assigned",
  "next_action": "Precise recommended next step",
  "sla_response_time": "Immediate (<1 hour)" | "Within 24 hours" | "Automated Nurture (7 days)"
}}
"""

        models_to_try = [self.primary_model] + [m for m in FALLBACK_MODELS if m != self.primary_model]

        for model in models_to_try:
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a professional B2B lead qualification AI engine. You must output strictly valid JSON conforming to the requested schema.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        response_format={"type": "json_object"},
                        temperature=0.1,
                    )

                    content = response.choices[0].message.content
                    raw_data = json.loads(content)

                    # Compute and normalize scores deterministically
                    fit_breakdown_raw = raw_data.get("fit_breakdown", {})
                    intent_breakdown_raw = raw_data.get("intent_breakdown", {})

                    fit_sub_total = (
                        fit_breakdown_raw.get("company_size_score", 0)
                        + fit_breakdown_raw.get("seniority_score", 0)
                        + fit_breakdown_raw.get("industry_fit_score", 0)
                    )
                    intent_sub_total = (
                        intent_breakdown_raw.get("behavior_signal_score", 0)
                        + intent_breakdown_raw.get("urgency_timeline_score", 0)
                        + intent_breakdown_raw.get("budget_readiness_score", 0)
                    )

                    fit_score = raw_data.get("fit_score", fit_sub_total)
                    intent_score = raw_data.get("intent_score", intent_sub_total)

                    # Clamp scores within legal ranges
                    fit_score = max(0, min(50, int(fit_score)))
                    intent_score = max(0, min(50, int(intent_score)))
                    total_score = max(0, min(100, fit_score + intent_score))

                    # Strict tier calculation guardrail
                    if total_score >= HOT_THRESHOLD:
                        tier = "HOT"
                    elif total_score >= WARM_THRESHOLD:
                        tier = "WARM"
                    else:
                        tier = "COLD"

                    raw_data["fit_score"] = fit_score
                    raw_data["intent_score"] = intent_score
                    raw_data["total_score"] = total_score
                    raw_data["tier"] = tier

                    # Validate with Pydantic
                    evaluation = LeadEvaluation(**raw_data)
                    return evaluation

                except Exception as e:
                    err_str = str(e).lower()
                    if "rate limit" in err_str or "429" in err_str:
                        wait_sec = 2 ** (attempt + 1)
                        time.sleep(wait_sec)
                    elif attempt == max_retries - 1:
                        # Try next model in fallback list
                        break
                    else:
                        time.sleep(1)

        return None

    def process_batch(self, leads: List[Dict[str, Any]], delay_between_calls: float = 0.5) -> List[Dict[str, Any]]:
        """
        Processes a list of leads, computes qualification scores, ranks them,
        and returns the enriched ordered list.
        """
        processed_leads = []
        total = len(leads)

        for i, lead in enumerate(leads, 1):
            lead_id = lead.get("id", f"L-{i:03d}")
            name = lead.get("name", "Unknown")
            company = lead.get("company", "Unknown")
            safe_print(f"[{i}/{total}] Evaluating {lead_id}: {name} ({company})...")

            evaluation = self.evaluate_lead(lead)

            if evaluation:
                eval_dict = evaluation.model_dump()
                # Create clean combined record
                lead_result = {
                    **lead,
                    "fit_score": eval_dict["fit_score"],
                    "intent_score": eval_dict["intent_score"],
                    "total_score": eval_dict["total_score"],
                    "tier": eval_dict["tier"],
                    "next_action": eval_dict["next_action"],
                    "rationale": eval_dict["rationale"],
                    "evaluation": eval_dict,
                }
                processed_leads.append(lead_result)
            else:
                safe_print(f"  [WARNING] Failed to evaluate lead {lead_id}.")

            if delay_between_calls > 0:
                time.sleep(delay_between_calls)

        # Sort descending by total score, then fit score, then intent score
        processed_leads.sort(
            key=lambda x: (x.get("total_score", 0), x.get("fit_score", 0), x.get("intent_score", 0)),
            reverse=True,
        )

        return processed_leads
