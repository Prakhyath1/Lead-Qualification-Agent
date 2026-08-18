# Engineering Design Decisions & Technical Tradeoffs

This document outlines the architectural choices, tradeoffs, and production roadmap for the **Lead Qualification AI Agent**, prepared for the **Rooman AI Challenge (Junior AI Research Associate Selection Round)**.

---

## 1. LLM Model Selection & Inference Platform

### Choice: Groq Cloud LPU Inference (`qwen/qwen3.6-27b` / `openai/gpt-oss-120b` / `openai/gpt-oss-20b`)

| Dimension | Groq LPU (Chosen) | OpenAI GPT-4o / Claude 3.5 | Local Ollama (e.g. Llama 3 8B) |
| :--- | :--- | :--- | :--- |
| **Inference Latency** | **~200–400 ms per lead** | ~1.5–3.0 s per lead | Dependent on local hardware (GPU required) |
| **Cost & Accessibility** | **Free tier available** (Zero barriers for reviewers) | Paid API key required ($5–$15 per 1k runs) | Free, but high local setup friction for evaluators |
| **JSON Schema Adherence** | **High** (Native `response_format={"type": "json_object"}`) | High (Structured Outputs) | Moderate (Prone to markdown syntax wrapping) |
| **Throughput** | **500+ tokens/sec** | ~80–120 tokens/sec | ~30–60 tokens/sec |

### Tradeoff Analysis:
- **Why Groq?** Reviewers evaluate code by running it immediately from the README. Choosing Groq enables any reviewer to obtain a free instant API key with zero billing friction while delivering sub-second inference speeds.
- **Why Model Fallbacks?** Free-tier APIs occasionally experience rate limits or model updates. We engineered an automatic **fallback chain** (`qwen/qwen3.6-27b` $\rightarrow$ `openai/gpt-oss-120b` $\rightarrow$ `openai/gpt-oss-20b` $\rightarrow$ `groq/compound`) with exponential backoff retries to guarantee zero-crash execution.

---

## 2. Structured Outputs vs. Function Calling

### Choice: Strict JSON Object Mode with Pydantic Schema Validation

- **Alternative 1: Function Calling / Tool Calling** — High overhead; requires registering custom tool definitions and parsing tool call arguments.
- **Alternative 2: Raw Text Generation** — Brittle; requires regex parsing and frequently fails on unexpected formatting.
- **Our Approach: Prompt-Grounded JSON + Pydantic Validation**:
  - We prompt the model with explicit schema constraints and grounding from `SCORING_LOGIC.md`.
  - The raw JSON payload is parsed into Pydantic models (`LeadEvaluation`, `FitBreakdown`, `IntentBreakdown`).
  - If field normalization is needed, Pydantic field validators automatically correct casing and types.

---

## 3. Hybrid AI Scoring vs. Pure Machine Learning / Pure Rules

### Architectural Decision:

```
                      ┌────────────────────────────┐
                      │ Inbound Lead (Raw / Form)  │
                      └─────────────┬──────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │    LLM Cognitive Layer     │
                      │ (Extracts nuance, intent,  │
                      │  urgency, & disqualifiers) │
                      └─────────────┬──────────────┘
                                    │ (Sub-scores)
                                    ▼
                      ┌────────────────────────────┐
                      │  Deterministic Guardrails  │
                      │ • Sub-score summation      │
                      │ • Hard clamping (0-50)     │
                      │ • Rule-based tier mapping  │
                      └─────────────┬──────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │ Final Verified Lead Record │
                      └────────────────────────────┘
```

- **Why Not Pure Rules (Regex / Point Systems)?**
  - Rigid point systems fail on qualitative notes (e.g. *"Our current contract expires in 45 days, need urgent API rollout"* vs *"Just browsing for school project"*). Natural language reasoning is required to interpret context and tone.
- **Why Not Pure Unchecked LLM?**
  - LLMs can occasionally suffer from minor arithmetic inconsistencies (e.g. outputting Fit=45, Intent=40, but Total=90 instead of 85).
- **Our Hybrid Solution**:
  - We let the LLM evaluate qualitative signals into granular sub-scores (`company_size_score`, `seniority_score`, `behavior_signal_score`, etc.).
  - We apply a **deterministic calculation layer** in Python that verifies `total_score = fit_score + intent_score` and enforces strict tier boundaries ($\ge 80 \implies \text{HOT}$, $\ge 50 \implies \text{WARM}$, $< 50 \implies \text{COLD}$). This eliminates AI hallucinations in final numbers.

---

## 4. Input Flexibility: Structured vs Unstructured Inbound

- **Challenge Requirement:** *"Take lead details (form data, notes, or email text) as input."*
- **Implementation:**
  - `data/leads.json` & `data/leads.csv` provide batch structured inputs.
  - `src/text_parser.py` implements an autonomous extractor capable of taking **unstructured raw emails, transcribed voicemails, or messy form notes** and structuring them before qualification.
  - The CLI supports `--text` and `--interactive` modes for instantaneous evaluation of single raw text inputs.

---

## 5. Limitations & Production Roadmap

If deploying this agent in an enterprise B2B production environment, we would implement the following enhancements:

1. **CRM & Webhook Ingestion**:
   - Deploy as a FastAPI / Cloud Run microservice listening to HubSpot / Salesforce / Segment webhooks on new `lead.created` events.
2. **Autonomous Lead Enrichment**:
   - Connect to Apollo.io, Clearbit, or LinkedIn APIs to enrich firmographic data (annual revenue, tech stack, funding stage) before LLM scoring.
3. **Vector Database / RAG for Custom ICPs**:
   - Store historical won/lost deal transcripts in a vector database (e.g. Pinecone / ChromaDB) to perform few-shot dynamic retrieval against historical closed-won patterns.
4. **Automated SDR Draft Email Generation**:
   - Extend the agent to draft personalized outreach emails tailored to the specific pain points and positive signals detected during qualification.
