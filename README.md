# 🏗️ InfraPulse v2.0 — Agentic AI Tender Automation

**ET GenAI Hackathon 2026 | Phase 2 Submission**
**Team:** InfraPulse | Amrita Vishwa Vidyapeetham, Amritapuri, Kerala
**Participant:** Lokesh Nalla
**Problem Statement:** PS-2 — Agentic AI for Autonomous Enterprise Workflows

---

## 🚀 What is InfraPulse?

InfraPulse is a **Multi-Agent AI system** that automates the full lifecycle of municipal road repair tender generation — from detecting a defect in a CCTV camera feed to producing a legally compliant, engineer-approved work order PDF — in under **5 minutes**, replacing a process that previously took **3–4 days** of manual work.

---

## 🤖 Agent Architecture

```
📡 Municipal CCTV Network (5 cameras)
           │
           ▼ Engineer selects camera via Control Room Dashboard
           │
┌──────────────────────────────────────────────┐
│           OrchestratorAgent                  │
│  Coordinates pipeline · Tracks recoveries    │
└───────┬──────────────┬───────────────┬───────┘
        │              │               │
        ▼              ▼               ▼
  ┌───────────┐  ┌───────────┐  ┌──────────────────┐
  │VisionAgent│  │ CostAgent │  │ ComplianceAgent  │
  │Llama 4    │  │ SOR-2025  │  │ CPWD Norms       │
  │Scout      │  │ + LLM     │  │ Legal Clauses    │
  └───────────┘  └───────────┘  └──────────────────┘
        │              │               │
        └──────────────┴───────────────┘
                       │
                       ▼
             👷 Engineer Reviews & Approves
                       │
                       ▼
            📄 Signed Work Order PDF
            📋 Audit Trail (CSV Export)
```

### The 4 Agents:
| Agent | Model | Job |
|---|---|---|
| **OrchestratorAgent** | Pipeline controller | Coordinates all agents, tracks recoveries, compiles final work order |
| **VisionAgent** | Llama 4 Scout (Vision) via Groq | Analyzes camera feed image — defect type, severity, area, safety risk |
| **CostAgent** | Llama 3.3 70B via Groq + SOR DB | Cost estimation, priority scoring, SLA, contractor routing |
| **ComplianceAgent** | Llama 3 8B via Groq | CPWD regulatory check, legal clauses, audit requirement |

---

## ⚙️ Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/your-username/infrapulse.git
cd infrapulse
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get a FREE Groq API key
- Go to [console.groq.com](https://console.groq.com)
- Sign up (free) → API Keys → Create API Key
- Copy the key starting with `gsk_...`

### 4. Run the app
```bash
streamlit run app.py
```

### 5. Enter your API key
- Paste your Groq key in the **sidebar** when the app opens
- The key is never stored anywhere — it only lives in your browser session

---

## 📁 File Structure
```
infrapulse/
├── app.py                                ← Main Streamlit application
├── requirements.txt                      ← Python dependencies
├── README.md                             ← This file
├── InfraPulse_Architecture_Document.pdf  ← Agent architecture doc
├── InfraPulse_Impact_Model.pdf           ← Business impact model
└── camera_feeds/
    ├── cam_001.jpg   ← MG Road Junction
    ├── cam_002.jpg   ← Silk Board Flyover
    ├── cam_003.jpg   ← Mysore Road
    ├── cam_004.jpg   ← KR Puram Bridge
    └── cam_005.jpg   ← Tumkur Road NH-48
```

---

## 📊 PS-2 Evaluation Criteria

| Criteria | How InfraPulse Addresses It |
|---|---|
| **Depth of autonomy** | 4 agents complete the full workflow — image to signed PDF — with zero manual steps until final approval |
| **Quality of error recovery** | VisionAgent falls back to text model; CostAgent falls back to rule-based scoring; all recoveries logged |
| **Auditability** | Every agent decision logged with timestamp, agent, action, result, status — exportable CSV + embedded in PDF |
| **Real-world applicability** | SOR-2025 rates, CPWD compliance, municipal work order format, 5-camera CCTV demo network |

---

## 🎯 Key Features

- **Engineer Control Room** — Filter cameras by zone and severity, sort by priority score
- **Live Camera Network** — 5 geo-tagged cameras across Bengaluru with real GPS coordinates
- **Self-correcting pipeline** — Agents recover automatically from API failures
- **Immutable audit trail** — Every decision logged and exportable
- **One-click PDF** — Signed work order with full audit trail embedded
- **Human-in-the-loop** — Engineer approval required before PDF issuance

---

## 💰 Impact (Summary)

| Metric | Result |
|---|---|
| Time-to-tender | 4.2 days to under 5 minutes (99.9% faster) |
| Engineer hours saved | ~32,800 hrs/year (~16 FTEs) |
| Annual cost saving | ~INR 64 Crore (Bengaluru scale) |
| CO2 prevented | ~905 tonnes/year |

*See `InfraPulse_Impact_Model.pdf` for full calculations and assumptions.*

---

## 🌱 Sustainability
Faster repairs prevent minor defects from escalating to full resurfacing — saving ~14.5 kg CO2 per sqm of timely repair. InfraPulse tracks cumulative CO2 saved per session in the sidebar.

---

*Built with Groq + Llama 4 Scout + Streamlit | ET GenAI Hackathon 2026*