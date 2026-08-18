import os
import sys
import json
import csv
from pathlib import Path
from typing import List, Dict, Any

# Ensure standard output uses UTF-8 to prevent Windows charmap/cp1252 UnicodeEncodeError
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def safe_print(message: str = ""):
    """Safely prints text to stdout handling any Windows terminal encoding anomalies."""
    try:
        print(message, flush=True)
    except UnicodeEncodeError:
        # Fallback to ascii replacement if terminal cannot handle specific glyphs
        clean_text = message.encode("ascii", errors="replace").decode("ascii")
        print(clean_text, flush=True)


def load_leads_from_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Loads leads from either a JSON or CSV file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found at: {path}")

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file must contain a list of lead objects.")
            return data

    elif path.suffix.lower() == ".csv":
        leads = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append(dict(row))
        return leads

    else:
        raise ValueError(f"Unsupported file format: '{path.suffix}'. Please provide .json or .csv")


def export_to_json(data: List[Dict[str, Any]], output_path: Path):
    """Exports processed leads to formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def export_to_csv(data: List[Dict[str, Any]], output_path: Path):
    """Exports processed leads to a flattened CSV spreadsheet for sales teams."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        return

    fieldnames = [
        "rank",
        "id",
        "name",
        "company",
        "job_title",
        "company_size",
        "industry",
        "total_score",
        "tier",
        "fit_score",
        "intent_score",
        "sla_response_time",
        "next_action",
        "rationale",
        "key_positive_signals",
        "red_flags",
    ]

    rows = []
    for idx, item in enumerate(data, 1):
        eval_data = item.get("evaluation", {})
        pos_signals = ", ".join(eval_data.get("key_positive_signals", []))
        red_flags = ", ".join(eval_data.get("red_flags", []))

        rows.append({
            "rank": idx,
            "id": item.get("id", ""),
            "name": item.get("name", ""),
            "company": item.get("company", ""),
            "job_title": item.get("job_title", ""),
            "company_size": item.get("company_size", ""),
            "industry": item.get("industry", ""),
            "total_score": item.get("total_score", eval_data.get("total_score", 0)),
            "tier": item.get("tier", eval_data.get("tier", "COLD")),
            "fit_score": item.get("fit_score", eval_data.get("fit_score", 0)),
            "intent_score": item.get("intent_score", eval_data.get("intent_score", 0)),
            "sla_response_time": eval_data.get("sla_response_time", "24 hours"),
            "next_action": eval_data.get("next_action", item.get("next_action", "")),
            "rationale": eval_data.get("rationale", item.get("rationale", "")),
            "key_positive_signals": pos_signals,
            "red_flags": red_flags,
        })

    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_markdown_report(data: List[Dict[str, Any]], output_path: Path):
    """Generates an executive-ready Markdown qualification summary report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    total_leads = len(data)
    if total_leads == 0:
        return

    hot_leads = [d for d in data if d.get("tier") == "HOT"]
    warm_leads = [d for d in data if d.get("tier") == "WARM"]
    cold_leads = [d for d in data if d.get("tier") == "COLD"]

    avg_score = sum(d.get("total_score", 0) for d in data) / total_leads
    avg_fit = sum(d.get("fit_score", 0) for d in data) / total_leads
    avg_intent = sum(d.get("intent_score", 0) for d in data) / total_leads

    report_lines = [
        "# Inbound Lead Qualification & Triage Executive Report",
        "",
        f"**Generated:** Automatically by Lead Qualification AI Agent  ",
        f"**Total Inbound Leads Evaluated:** {total_leads}  ",
        f"**Average Lead Quality Score:** {avg_score:.1f}/100 (Fit: {avg_fit:.1f}/50 | Intent: {avg_intent:.1f}/50)",
        "",
        "---",
        "",
        "## Executive Summary & Tier Distribution",
        "",
        "| Tier | Count | Percentage | Primary Sales Action |",
        "| :--- | :--- | :--- | :--- |",
        f"| 🔥 **HOT** (80-100 pts) | **{len(hot_leads)}** | {len(hot_leads)/total_leads*100:.1f}% | Immediate AE Outreach / Discovery Call (SLA: <1 hr) |",
        f"| ⚡ **WARM** (50-79 pts) | **{len(warm_leads)}** | {len(warm_leads)/total_leads*100:.1f}% | SDR Nurturing & Custom Case Study (SLA: <24 hrs) |",
        f"| ❄️ **COLD** (0-49 pts) | **{len(cold_leads)}** | {len(cold_leads)/total_leads*100:.1f}% | Automated Marketing Drip / Disqualified |",
        "",
        "---",
        "",
        "## Priority Action Playbook (🔥 HOT Leads — Call First)",
        "",
    ]

    if hot_leads:
        for idx, lead in enumerate(hot_leads, 1):
            eval_data = lead.get("evaluation", {})
            pos_signals = eval_data.get("key_positive_signals", [])
            pos_str = "; ".join(pos_signals) if pos_signals else "High ICP alignment & active buying signals"
            report_lines.extend([
                f"### {idx}. {lead.get('name')} — {lead.get('company')} ({lead.get('job_title')})",
                f"- **Score:** `{lead.get('total_score')}/100` (Fit: `{lead.get('fit_score')}/50`, Intent: `{lead.get('intent_score')}/50`)",
                f"- **SLA Window:** `{eval_data.get('sla_response_time', 'Immediate (<1 hour)')}`",
                f"- **Recommended Next Step:** **{lead.get('next_action')}**",
                f"- **Key Conversion Drivers:** {pos_str}",
                f"- **Agent Rationale:** {lead.get('rationale')}",
                "",
            ])
    else:
        report_lines.append("*No HOT leads identified in this batch.*\n")

    report_lines.extend([
        "---",
        "",
        "## Full Scored & Ranked Leads Table",
        "",
        "| Rank | Score | Tier | Lead Name | Company | Role | Industry | Recommended Action |",
        "| :---: | :---: | :---: | :--- | :--- | :--- | :--- | :--- |",
    ])

    for idx, lead in enumerate(data, 1):
        tier = lead.get("tier", "COLD")
        icon = "🔥" if tier == "HOT" else ("⚡" if tier == "WARM" else "❄️")
        name = lead.get("name", "N/A")
        comp = lead.get("company", "N/A")
        role = lead.get("job_title", "N/A")
        ind = lead.get("industry", "N/A")
        action = (lead.get("next_action") or "Nurture")[:45] + "..." if len(lead.get("next_action", "")) > 45 else lead.get("next_action", "Nurture")
        score = lead.get("total_score", 0)
        report_lines.append(f"| {idx} | **{score}** | {icon} {tier} | {name} | {comp} | {role} | {ind} | {action} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## Disqualification & Risk Flags Summary",
        "",
    ])

    flagged_leads = [d for d in data if d.get("evaluation", {}).get("red_flags")]
    if flagged_leads:
        for lead in flagged_leads:
            flags = lead.get("evaluation", {}).get("red_flags", [])
            report_lines.append(f"- **{lead.get('name')} ({lead.get('company')}):** {', '.join(flags)}")
    else:
        report_lines.append("- *No specific disqualification flags recorded.*")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
