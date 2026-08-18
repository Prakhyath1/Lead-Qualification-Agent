import json
import os
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

from src.config import (
    validate_api_key,
    PRIMARY_MODEL,
    DEFAULT_INPUT_FILE,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_CSV,
    FALLBACK_MODELS,
    BASE_DIR,
)
from src.scorer import LeadScorer
from src.text_parser import extract_lead_from_text
from src.utils import load_leads_from_file, export_to_csv, export_to_json

load_dotenv()

st.set_page_config(
    page_title="AI Lead Qualification Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
    }
    .tier-hot {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .tier-warm {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .tier-cold {
        background-color: #E2E8F0;
        color: #334155;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar Configuration
st.sidebar.title("⚙️ Agent Settings")
api_key_input = st.sidebar.text_input(
    "Groq API Key",
    value=os.getenv("GROQ_API_KEY", ""),
    type="password",
    help="Get a free key from console.groq.com",
)
selected_model = st.sidebar.selectbox(
    "LLM Model",
    options=[PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL],
    index=0,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Challenge Submission")
st.sidebar.info(
    "**Rooman AI Challenge**\n\n"
    "Agent: **Lead Qualification Agent**\n\n"
    "Stack: Python, Groq LLM, Pydantic, Streamlit"
)

# Header
st.markdown('<div class="main-header">⚡ Inbound Lead Qualification AI Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated AI scoring, ICP fit analysis, buying intent detection, and priority SDR triage.</div>',
    unsafe_allow_html=True,
)

# Tabs
tab1, tab2, tab3 = st.tabs(["📋 Batch Lead Dashboard", "✍️ Live Lead Qualifier", "📖 Scoring Methodology"])

# Initialize Scorer
@st.cache_resource
def get_scorer(api_key: str, model_name: str):
    if not api_key:
        return None
    return LeadScorer(api_key=api_key, model_name=model_name)

scorer = get_scorer(api_key_input, selected_model) if api_key_input else None


# TAB 1: Batch Dashboard
with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("Ranked Inbound Leads")
    with col2:
        run_batch_btn = st.button("🚀 Re-Run Batch Scoring", type="primary")

    # Load data
    ranked_data = []
    if DEFAULT_OUTPUT_JSON.exists():
        try:
            with open(DEFAULT_OUTPUT_JSON, "r", encoding="utf-8") as f:
                ranked_data = json.load(f)
        except Exception:
            ranked_data = []

    if run_batch_btn:
        if not scorer:
            st.error("Please provide a valid Groq API Key in the sidebar.")
        else:
            with st.spinner("Evaluating leads via Groq LLM..."):
                leads_input = load_leads_from_file(DEFAULT_INPUT_FILE)
                ranked_data = scorer.process_batch(leads_input, delay_between_calls=0.3)
                export_to_json(ranked_data, DEFAULT_OUTPUT_JSON)
                export_to_csv(ranked_data, DEFAULT_OUTPUT_CSV)
                st.success(f"Successfully evaluated and ranked {len(ranked_data)} leads!")

    if ranked_data:
        # Top Metric Cards
        total_count = len(ranked_data)
        hot_count = sum(1 for d in ranked_data if d.get("tier") == "HOT")
        warm_count = sum(1 for d in ranked_data if d.get("tier") == "WARM")
        cold_count = sum(1 for d in ranked_data if d.get("tier") == "COLD")
        avg_score = sum(d.get("total_score", 0) for d in ranked_data) / max(total_count, 1)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Leads", total_count)
        m2.metric("🔥 HOT Leads", hot_count, f"{hot_count/total_count*100:.0f}%")
        m3.metric("⚡ WARM Leads", warm_count, f"{warm_count/total_count*100:.0f}%")
        m4.metric("❄️ COLD Leads", cold_count, f"{cold_count/total_count*100:.0f}%")
        m5.metric("Avg Quality Score", f"{avg_score:.1f}/100")

        st.markdown("---")

        # Filters
        f_col1, f_col2 = st.columns([1, 3])
        with f_col1:
            tier_filter = st.multiselect("Filter by Tier", ["HOT", "WARM", "COLD"], default=["HOT", "WARM", "COLD"])
        with f_col2:
            search_query = st.text_input("🔍 Search Leads", placeholder="Search by name, company, or role...")

        # Filter dataset
        filtered = [
            d for d in ranked_data
            if d.get("tier") in tier_filter
            and (
                search_query.lower() in d.get("name", "").lower()
                or search_query.lower() in d.get("company", "").lower()
                or search_query.lower() in d.get("job_title", "").lower()
                or search_query.lower() in d.get("industry", "").lower()
            )
        ]

        # Table Display
        table_rows = []
        for idx, item in enumerate(filtered, 1):
            table_rows.append({
                "Rank": idx,
                "Score": item.get("total_score"),
                "Tier": item.get("tier"),
                "Name": item.get("name"),
                "Company": item.get("company"),
                "Title": item.get("job_title"),
                "Industry": item.get("industry"),
                "Fit": item.get("fit_score"),
                "Intent": item.get("intent_score"),
                "Next Action": item.get("next_action"),
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, hide_index=True)

        # Detailed Lead Card Expanders
        st.markdown("### 🔍 Lead Deep-Dive & Reasoning")
        for lead in filtered:
            tier = lead.get("tier", "COLD")
            icon = "🔥" if tier == "HOT" else ("⚡" if tier == "WARM" else "❄️")
            with st.expander(f"{icon} [{tier} - Score: {lead.get('total_score')}/100] {lead.get('name')} | {lead.get('company')} ({lead.get('job_title')})"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🏢 Company:** {lead.get('company')} ({lead.get('company_size')} employees)")
                    st.markdown(f"**💼 Industry:** {lead.get('industry')}")
                    st.markdown(f"**👤 Title:** {lead.get('job_title')}")
                    st.markdown(f"**💰 Budget Status:** {lead.get('budget_status', 'N/A')}")
                    st.markdown(f"**⏱️ Timeline:** {lead.get('timeline', 'N/A')}")
                with c2:
                    st.markdown(f"**🎯 Fit Score:** `{lead.get('fit_score')}/50`")
                    st.markdown(f"**🚀 Intent Score:** `{lead.get('intent_score')}/50`")
                    eval_data = lead.get("evaluation", {})
                    st.markdown(f"**⚡ SLA Response Window:** `{eval_data.get('sla_response_time', 'Within 24 hours')}`")
                    st.markdown(f"**👉 Recommended Next Action:** **{lead.get('next_action')}**")

                st.markdown(f"**📝 AI Rationale:** {lead.get('rationale')}")

                pos_signals = eval_data.get("key_positive_signals", [])
                red_flags = eval_data.get("red_flags", [])

                if pos_signals:
                    st.markdown(f"**✅ Positive Signals:** {', '.join(pos_signals)}")
                if red_flags:
                    st.markdown(f"**⚠️ Risk/Disqualification Flags:** {', '.join(red_flags)}")

        # Download Buttons
        st.markdown("---")
        d1, d2 = st.columns(2)
        with d1:
            json_bytes = json.dumps(ranked_data, indent=2).encode("utf-8")
            st.download_button(
                "📥 Download Ranked Leads (JSON)",
                data=json_bytes,
                file_name="ranked_leads.json",
                mime="application/json",
            )
        with d2:
            if DEFAULT_OUTPUT_CSV.exists():
                with open(DEFAULT_OUTPUT_CSV, "rb") as f:
                    csv_bytes = f.read()
                st.download_button(
                    "📥 Download Ranked Leads (CSV)",
                    data=csv_bytes,
                    file_name="ranked_leads.csv",
                    mime="text/csv",
                )

    else:
        st.info("No scored leads found yet. Click 'Re-Run Batch Scoring' above or run `python main.py` in your terminal.")


# TAB 2: Live Lead Qualifier
with tab2:
    st.subheader("Test Any Inbound Inquiry Live")
    st.write("Paste a raw customer email, form message, or sales notes to test real-time AI parsing and qualification.")

    sample_email_default = """Hi Sales Team,

I'm Sarah Jenkins, VP of Engineering at TechFlow Inc. (around 750 employees). We are currently auditing our inbound lead processing stack as our contract with our legacy vendor ends next month. We need a reliable, API-first AI agent that can parse unstructured lead data and integrate into our custom CRM.

We have an approved $80k annual budget and would like to schedule a technical discovery call this week with your solution architect.

Best,
Sarah Jenkins
VP of Engineering, TechFlow Inc."""

    raw_text_input = st.text_area("Inbound Message / Email / Notes", value=sample_email_default, height=200)

    if st.button("⚡ Qualify Inbound Lead", type="primary"):
        if not scorer:
            st.error("Please configure your Groq API Key in the sidebar.")
        elif not raw_text_input.strip():
            st.warning("Please enter some text to qualify.")
        else:
            with st.spinner("Extracting structured profile & qualifying lead..."):
                lead_obj = extract_lead_from_text(raw_text_input, scorer.client, scorer.primary_model)
                if not lead_obj:
                    st.error("Could not parse lead information from text.")
                else:
                    lead_dict = lead_obj.model_dump()
                    eval_result = scorer.evaluate_lead(lead_dict)
                    if not eval_result:
                        st.error("Evaluation failed.")
                    else:
                        res = eval_result.model_dump()
                        tier = res["tier"]
                        color_class = "tier-hot" if tier == "HOT" else ("tier-warm" if tier == "WARM" else "tier-cold")
                        icon = "🔥" if tier == "HOT" else ("⚡" if tier == "WARM" else "❄️")

                        st.success("Lead Qualified Successfully!")
                        st.markdown(f"### {icon} Tier: <span class='{color_class}'>{tier}</span> | Score: `{res['total_score']}/100`", unsafe_allow_html=True)

                        c1, c2, c3 = st.columns(3)
                        c1.metric("Fit Score", f"{res['fit_score']}/50")
                        c2.metric("Intent Score", f"{res['intent_score']}/50")
                        c3.metric("SLA Window", res.get("sla_response_time", "24 hours"))

                        st.markdown(f"**🏢 Extracted Entity:** {lead_dict.get('name')} | {lead_dict.get('company')} ({lead_dict.get('job_title')}) - {lead_dict.get('company_size')} employees")
                        st.markdown(f"**👉 Recommended Next Action:** **{res['next_action']}**")
                        st.markdown(f"**📝 AI Rationale:** {res['rationale']}")

                        if res.get("key_positive_signals"):
                            st.info(f"**Positive Signals:** {', '.join(res['key_positive_signals'])}")
                        if res.get("red_flags"):
                            st.warning(f"**Red Flags / Disqualifiers:** {', '.join(res['red_flags'])}")


# TAB 3: Scoring Methodology
with tab3:
    st.subheader("Scoring Methodology & Rubric")
    if (BASE_DIR / "SCORING_LOGIC.md").exists():
        with open(BASE_DIR / "SCORING_LOGIC.md", "r", encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.write("Scoring logic documentation not found.")
