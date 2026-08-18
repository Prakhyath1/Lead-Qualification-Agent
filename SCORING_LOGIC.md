# Lead Qualification & Scoring Methodology

This document outlines the evaluation framework, mathematical weights, and triage logic used by the **Lead Qualification AI Agent** to score and prioritize inbound leads for B2B sales teams.

---

## 1. Overview & Architecture

The qualification agent analyzes inbound sales signals across two independent 50-point pillars:
1. **Fit Score (0 – 50 Points)**: Evaluates firmographic alignment with our Ideal Customer Profile (ICP).
2. **Intent Score (0 – 50 Points)**: Measures buying signals, timeline urgency, and commercial commitment.

$$\text{Total Score} = \text{Fit Score (0-50)} + \text{Intent Score (0-50)} \in [0, 100]$$

---

## 2. Fit Score Matrix (Max 50 Points)

The Fit score evaluates whether the prospect's organization and persona match our high-value target customer profile.

### A. Company Scale & Employee Count (Max 15 Pts)
| Company Size | Score Range | Description |
| :--- | :---: | :--- |
| **Enterprise (1,000+ employees)** | **13 – 15 pts** | High lifetime value, large seat expansion opportunity. |
| **Mid-Market (200 – 999 employees)** | **10 – 12 pts** | Strong operational fit, rapid deal velocity. |
| **Growth SMB (50 – 199 employees)** | **6 – 9 pts** | Emerging scale-up, moderate initial deal size. |
| **Micro / Seed (1 – 49 employees)** | **1 – 5 pts** | Low seat counts, high sensitivity to price. |
| **Solo / Freelancer / Unknown** | **0 pts** | Non-viable for B2B enterprise sales. |

### B. Seniority & Decision-Making Authority (Max 20 Pts)
| Role Seniority | Score Range | Description |
| :--- | :---: | :--- |
| **C-Level / Founder / VP** (CRO, CTO, VP Eng, COO) | **18 – 20 pts** | Direct budget owner and final sign-off authority. |
| **Director / Head of Department** | **14 – 17 pts** | Departmental champion with purchasing influence. |
| **Manager / Team Lead** | **8 – 13 pts** | Operational evaluator, requires executive sponsorship. |
| **Individual Contributor / Engineer** | **3 – 7 pts** | Technical tester without purchasing power. |
| **Student / Intern / Unverified** | **0 pts** | Zero purchasing authority. |

### C. Industry ICP Alignment (Max 15 Pts)
| Industry Sector | Score Range | Description |
| :--- | :---: | :--- |
| **Tier 1 ICP** (Software, Cloud, SaaS, FinTech, Cybersecurity) | **13 – 15 pts** | Core target vertical with highest conversion rates. |
| **Tier 2 ICP** (Logistics, Healthcare, Financial Services, Legal Tech) | **9 – 12 pts** | High compliance / complex automation requirements. |
| **Tier 3 (Adjacent)** (Manufacturing, E-commerce, Professional Services) | **5 – 8 pts** | Moderate applicability. |
| **Non-ICP** (Local Retail, Crafts, Restaurants, General Consumer) | **0 – 3 pts** | Mismatched product-market fit. |

---

## 3. Intent Score Matrix (Max 50 Points)

The Intent score assesses the lead's active engagement and proximity to a purchasing decision.

### A. Behavioral Action Signal Strength (Max 25 Pts)
| Signal Type | Score Range | Examples |
| :--- | :---: | :--- |
| **High-Intent Conversion** | **20 – 25 pts** | Requested live product demo, submitted RFP, visited pricing 3+ times in 48h, tested API sandbox. |
| **Mid-Intent Engagement** | **11 – 19 pts** | Attended technical webinar, downloaded security whitepaper, calculated ROI on pricing page. |
| **Low-Intent / Passive** | **1 – 10 pts** | Subscribed to general newsletter, read a single blog post, clicked top-of-funnel social ad. |
| **No Engagement / Spam** | **0 pts** | Blank form submissions, bot traffic. |

### B. Implementation Timeline & Urgency (Max 15 Pts)
| Timeline Window | Score Range | Description |
| :--- | :---: | :--- |
| **Immediate (Within 30 Days / Urgent)** | **13 – 15 pts** | Expiring vendor contract, executive mandate, Series C scale pressure. |
| **Short-Term (1 – 3 Months)** | **9 – 12 pts** | Active project evaluation for upcoming fiscal quarter. |
| **Medium-Term (3 – 6 Months)** | **5 – 8 pts** | Preliminary research, annual budgeting cycle. |
| **No Timeline / Browsing** | **0 – 3 pts** | No defined project dates. |

### C. Budget Readiness & Authority (Max 10 Pts)
| Budget Status | Score Range | Description |
| :--- | :---: | :--- |
| **Approved / Earmarked Budget** | **8 – 10 pts** | Dedicated capital allocated ($50k-$250k+). |
| **Discretionary / In Review** | **4 – 7 pts** | Departmental funds available pending ROI approval. |
| **Seeking Free / No Budget** | **0 – 2 pts** | Looking for free tier, educational grants, or under $50/mo. |

---

## 4. Red Flags & Automatic Disqualifiers

The AI agent checks for disqualification triggers and applies penalties or downward tier overrides:
- **Competitor Scouting**: Leads originating from direct competitor domains or rival product marketing teams are flagged and routed to Competitive Intelligence.
- **Academic / Non-Commercial**: Students or researchers requesting free tokens for thesis benchmarking.
- **Disposable / Temp Email Domains**: Inbounds from `@10minutemail`, `@tempmail`, or unverified personal handles for enterprise products.
- **Off-Target Domain**: Inbounds requesting irrelevant services (e.g. lawn care software, mom-and-pop retail).

---

## 5. Tier Classification & SLA Triage Playbook

| Tier | Score Range | SLA Response Window | Recommended Sales Playbook |
| :--- | :---: | :---: | :--- |
| 🔥 **HOT** | **80 – 100** | **< 1 Hour** | **Direct AE Handoff**: Dedicated Account Executive schedules technical discovery call immediately. Prepare custom architectural demo and security docs. |
| ⚡ **WARM** | **50 – 79** | **< 24 Hours** | **SDR Qualification**: Sales Development Rep reaches out with targeted industry case study, ROI calculator, and invitation to scheduled group demo. |
| ❄️ **COLD** | **0 – 49** | **7-Day Drip** | **Automated Nurture**: Enrolled in automated email educational newsletter drip. Flagged disqualifiers are filtered out of active SDR queues. |
