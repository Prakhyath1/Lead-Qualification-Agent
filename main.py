import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

from src.config import (
    validate_api_key,
    PRIMARY_MODEL,
    DEFAULT_INPUT_FILE,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_CSV,
    DEFAULT_OUTPUT_REPORT,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_EMAILS_FILE,
)
from src.scorer import LeadScorer
from src.text_parser import extract_lead_from_text
from src.utils import (
    safe_print,
    load_leads_from_file,
    export_to_json,
    export_to_csv,
    generate_markdown_report,
)


def print_banner():
    safe_print("=" * 80)
    safe_print("           AI LEAD QUALIFICATION & SCORING AGENT")
    safe_print("   Rooman AI Challenge — Junior AI Research Associate Selection")
    safe_print("=" * 80)


def print_summary_table(leads: List[Dict[str, Any]]):
    safe_print("\n" + "=" * 90)
    safe_print(f"{'RANK':<5} {'SCORE':<7} {'TIER':<7} {'NAME':<20} {'COMPANY':<22} {'FIT/INTENT':<12} {'SLA':<12}")
    safe_print("-" * 90)

    for idx, lead in enumerate(leads, 1):
        tier = lead.get("tier", "COLD")
        icon = "[HOT]" if tier == "HOT" else ("[WARM]" if tier == "WARM" else "[COLD]")
        name = str(lead.get("name", "N/A"))[:18]
        comp = str(lead.get("company", "N/A"))[:20]
        score = lead.get("total_score", 0)
        fit = lead.get("fit_score", 0)
        intent = lead.get("intent_score", 0)
        eval_data = lead.get("evaluation", {})
        sla = eval_data.get("sla_response_time", "24h")[:10]

        safe_print(f"{idx:<5} {score:<7} {icon:<7} {name:<20} {comp:<22} {fit}/{intent:<9} {sla:<12}")

    safe_print("=" * 90)

    hot_leads = [l for l in leads if l.get("tier") == "HOT"]
    warm_leads = [l for l in leads if l.get("tier") == "WARM"]
    cold_leads = [l for l in leads if l.get("tier") == "COLD"]

    safe_print(f"\n[DISTRIBUTION] Total: {len(leads)} | Hot: {len(hot_leads)} | Warm: {len(warm_leads)} | Cold: {len(cold_leads)}")

    if hot_leads:
        safe_print("\n[PRIORITY ACTION PLAYBOOK - HOT LEADS]:")
        for lead in hot_leads:
            safe_print(f"  * {lead.get('name')} ({lead.get('company')}): {lead.get('next_action')}")


def run_interactive_mode(scorer: LeadScorer):
    safe_print("\n--- INTERACTIVE LEAD QUALIFICATION MODE ---")
    safe_print("Paste raw email text, sales inquiry, or type lead details below.")
    safe_print("Enter text and press Ctrl+Z (Windows) or Ctrl+D (Linux/Mac) then Enter when finished:")
    safe_print("-" * 60)

    try:
        lines = sys.stdin.read().strip()
    except Exception:
        lines = ""

    if not lines:
        safe_print("No input received. Exiting interactive mode.")
        return

    safe_print("\n[AI Agent] Parsing raw inquiry into structured lead profile...")
    lead_input = extract_lead_from_text(lines, scorer.client, scorer.primary_model)

    if not lead_input:
        safe_print("[ERROR] Could not parse lead from provided text.")
        return

    lead_dict = lead_input.model_dump()
    safe_print(f"Extracted Lead: {lead_dict.get('name')} from {lead_dict.get('company')} ({lead_dict.get('job_title')})")
    safe_print("[AI Agent] Qualifying lead against scoring rubric...\n")

    eval_result = scorer.evaluate_lead(lead_dict)
    if not eval_result:
        safe_print("[ERROR] Evaluation failed.")
        return

    res = eval_result.model_dump()
    safe_print("=" * 60)
    safe_print(f"QUALIFICATION RESULT: {res['tier']} (Score: {res['total_score']}/100)")
    safe_print(f"- Fit Score:    {res['fit_score']}/50")
    safe_print(f"- Intent Score: {res['intent_score']}/50")
    safe_print(f"- Recommended SLA: {res.get('sla_response_time', 'N/A')}")
    safe_print(f"- Next Action:  {res['next_action']}")
    safe_print(f"- Rationale:    {res['rationale']}")
    if res.get("key_positive_signals"):
        safe_print(f"- Positive Signals: {', '.join(res['key_positive_signals'])}")
    if res.get("red_flags"):
        safe_print(f"- Red Flags: {', '.join(res['red_flags'])}")
    safe_print("=" * 60)


def run_single_text_mode(text: str, scorer: LeadScorer):
    safe_print(f"\n[AI Agent] Parsing and scoring single text inquiry...")
    lead_input = extract_lead_from_text(text, scorer.client, scorer.primary_model)
    if not lead_input:
        safe_print("[ERROR] Failed to extract structured fields from input text.")
        return

    lead_dict = lead_input.model_dump()
    eval_result = scorer.evaluate_lead(lead_dict)
    if not eval_result:
        safe_print("[ERROR] Failed to evaluate lead.")
        return

    res = eval_result.model_dump()
    safe_print("\n" + "=" * 65)
    safe_print(f"LEAD: {lead_dict.get('name')} | COMPANY: {lead_dict.get('company')} ({lead_dict.get('job_title')})")
    safe_print(f"TIER: {res['tier']} | TOTAL SCORE: {res['total_score']}/100 (Fit: {res['fit_score']}, Intent: {res['intent_score']})")
    safe_print(f"SLA:  {res.get('sla_response_time', 'Within 24 hours')}")
    safe_print(f"NEXT ACTION: {res['next_action']}")
    safe_print(f"RATIONALE:   {res['rationale']}")
    safe_print("=" * 65 + "\n")


def run_emails_batch_mode(scorer: LeadScorer, emails_path: Path):
    safe_print(f"\nLoading raw inbound emails from {emails_path}...")
    with open(emails_path, "r", encoding="utf-8") as f:
        emails = json.load(f)

    safe_print(f"Found {len(emails)} emails. Parsing and evaluating each...")
    extracted_leads = []
    for em in emails:
        raw_text = f"Subject: {em.get('subject')}\nFrom: {em.get('sender')}\n\n{em.get('body')}"
        lead_input = extract_lead_from_text(raw_text, scorer.client, scorer.primary_model)
        if lead_input:
            extracted_leads.append(lead_input.model_dump())

    safe_print(f"Extracted {len(extracted_leads)} structured leads. Scoring now...")
    ranked = scorer.process_batch(extracted_leads, delay_between_calls=0.5)
    print_summary_table(ranked)


def main():
    parser = argparse.ArgumentParser(
        description="Lead Qualification AI Agent — Qualifies and ranks inbound B2B sales leads.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=str(DEFAULT_INPUT_FILE),
        help=f"Path to input leads file (.json or .csv). Default: {DEFAULT_INPUT_FILE}",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"Directory to save outputs (.json, .csv, report.md). Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=PRIMARY_MODEL,
        help=f"Groq LLM model name to use. Default: {PRIMARY_MODEL}",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive single-lead evaluation mode.",
    )
    parser.add_argument(
        "--text",
        type=str,
        help="Qualify a single raw text / email inquiry directly from CLI.",
    )
    parser.add_argument(
        "--emails",
        action="store_true",
        help="Process raw inbound email dataset from data/inbound_emails.json.",
    )

    args = parser.parse_args()

    print_banner()

    # Validate API key
    api_key = validate_api_key()
    scorer = LeadScorer(api_key=api_key, model_name=args.model)

    if args.interactive:
        run_interactive_mode(scorer)
        return

    if args.text:
        run_single_text_mode(args.text, scorer)
        return

    if args.emails:
        run_emails_batch_mode(scorer, DEFAULT_EMAILS_FILE)
        return

    # Standard batch mode
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_print(f"Loading leads from: {input_path}")
    try:
        leads = load_leads_from_file(input_path)
    except Exception as e:
        safe_print(f"[ERROR] Failed to load leads: {e}")
        sys.exit(1)

    safe_print(f"Loaded {len(leads)} leads. Scoring via Groq LLM ({args.model})...\n")

    ranked_leads = scorer.process_batch(leads, delay_between_calls=0.4)

    # Export to all output formats
    output_json = output_dir / "ranked_leads.json"
    output_csv = output_dir / "ranked_leads.csv"
    output_report = output_dir / "qualification_report.md"

    export_to_json(ranked_leads, output_json)
    export_to_csv(ranked_leads, output_csv)
    generate_markdown_report(ranked_leads, output_report)

    safe_print("\n[SUCCESS] Processing Complete!")
    safe_print(f"  -> JSON Output:   {output_json}")
    safe_print(f"  -> CSV Output:    {output_csv}")
    safe_print(f"  -> Report Output: {output_report}")

    print_summary_table(ranked_leads)


if __name__ == "__main__":
    main()
