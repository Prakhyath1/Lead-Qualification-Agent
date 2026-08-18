import json
from typing import Optional
from groq import Groq
from src.models import LeadInput
from src.config import PRIMARY_MODEL, FALLBACK_MODELS


def extract_lead_from_text(raw_text: str, client: Groq, model: str = PRIMARY_MODEL) -> Optional[LeadInput]:
    """
    Uses the Groq LLM to parse an unstructured email, contact message, or sales note
    into a structured LeadInput object.
    """
    extraction_prompt = f"""
    You are an AI data extraction specialist for Sales Operations.
    Analyze the following raw inbound text (email, form submission, or transcript) and extract structured lead information.

    RAW TEXT:
    \"\"\"
    {raw_text}
    \"\"\"

    Extract the following fields into valid JSON:
    {{
      "id": "INBOUND-RAW",
      "name": "Full Name or Unknown",
      "company": "Company Name or Unknown",
      "company_size": "Estimated employee count or Unknown (e.g., '1-10', '50-200', '500-1000', '10000+')",
      "job_title": "Role/Title or Unknown",
      "industry": "Industry sector or Unknown",
      "email": "Email address if found or empty string",
      "intent_signals": "Extracted behavioral intent, actions mentioned, demo requests, etc.",
      "notes": "Contextual notes, specific requirements, pain points, or urgency mentioned",
      "budget_status": "Budget information if stated (e.g., 'Approved $50k', 'None', 'Seeking discount', or 'Unknown')",
      "timeline": "Implementation timeline if stated (e.g., 'Immediate', '3-6 months', or 'Unknown')"
    }}
    """

    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    
    for candidate_model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=candidate_model,
                messages=[
                    {"role": "system", "content": "You are a precise data extractor. You must respond in valid JSON format only."},
                    {"role": "user", "content": extraction_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            data = json.loads(response.choices[0].message.content)
            return LeadInput(**data)
        except Exception:
            continue

    return None
