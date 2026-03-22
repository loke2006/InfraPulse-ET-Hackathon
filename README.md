# 🏗️ InfraPulse v2.0 — Agentic AI Tender Automation

**ET GenAI Hackathon 2026 | Phase 2 Submission**
**Team:** InfraPulse | Amrita Vishwa Vidyapeetham, Amritapuri, Kerala
**Problem Statement:** PS-2 — Agentic AI for Autonomous Enterprise Workflows

---

## 🚀 What's New in v2

| Feature | v1 (Phase 1) | v2 (Phase 2) |
|---|---|---|
| AI Engine | Mock/Random | Real Groq API (Llama 4 Vision) |
| Architecture | Single script | 4-Agent Pipeline |
| Error Handling | None | Self-correcting with fallbacks |
| Audit Trail | None | Full immutable log (CSV export) |
| Compliance | Hardcoded | ComplianceAgent (LLM-powered) |
| Cost Scoring | Static lookup | Priority scoring via LLM |

---

## 🤖 Agent Architecture

```
📸 Site Image
     │
     ▼
┌─────────────────────────────────────────────────────┐
│              OrchestratorAgent                      │
│   Coordinates pipeline, handles failures            │
└─────────┬───────────────┬────────────────┬──────────┘
          │               │                │
          ▼               ▼                ▼
   ┌────────────┐  ┌────────────┐  ┌──────────────────┐
   │ VisionAgent│  │ CostAgent  │  │ ComplianceAgent  │
   │ Llama 4    │  │ SOR-2025   │  │ CPWD Norms       │
   │ Vision     │  │ + LLM      │  │ Regulatory Check │
   └────────────┘  └────────────┘  └──────────────────┘
          │               │                │
          └───────────────┴────────────────┘
                          │
                          ▼
                 📄 Signed Work Order PDF
                 📋 Audit Trail (CSV)
```

### Agents:
1. **VisionAgent** — Uses Llama 4 Scout (vision model) via Groq to classify defect type, severity, area, safety risk. Falls back to text-only model if vision fails.
2. **CostAgent** — Queries SOR-2025 rate database + LLM for priority scoring, SLA, contractor routing. Rule-based fallback included.
3. **ComplianceAgent** — Validates against CPWD norms, generates legal clauses, flags high-value tenders for audit.
4. **OrchestratorAgent** — Manages the pipeline, tracks recoveries, compiles final work order.

---

## ⚙️ Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Get a FREE Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Sign up (free) → Create API Key
- Copy the key starting with `gsk_...`

### 3. Run the app
```bash
streamlit run app.py
```

### 4. Enter API key
- Paste your Groq key in the **sidebar** (it's never stored)

---

## 📊 PS-2 Evaluation Criteria Coverage

| Criteria | How InfraPulse v2 Addresses It |
|---|---|
| **Depth of autonomy** | 4 agents complete the full workflow — from image to signed PDF — with zero manual steps until final approval |
| **Quality of error recovery** | VisionAgent has a text-only fallback; CostAgent has rule-based fallback; all recoveries logged |
| **Auditability** | Every agent decision logged with timestamp, agent name, action, result, status. Exportable as CSV and embedded in PDF |
| **Real-world applicability** | SOR-2025 rates, CPWD compliance, municipal work order format, contractor routing by tender value |

---

## 📁 File Structure
```
infrapulse_v2/
├── app.py              ← Main Streamlit application
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🌱 Sustainability Impact
Each repair prevents minor damage from escalating — InfraPulse estimates ~14.5 kg CO₂ saved per sqm of timely repair (vs delayed large-scale resurfacing).