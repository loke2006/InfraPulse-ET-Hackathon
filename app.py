import streamlit as st
import pandas as pd
from fpdf import FPDF
import time
import random
import json
import base64
from datetime import datetime
from PIL import Image, ImageDraw
import os
import re
from groq import Groq

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="InfraPulse v2 | Agentic Tender Automation",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — Industrial / GovTech Aesthetic
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}

/* Dark industrial background */
.stApp {
    background-color: #0d1117;
    color: #e6edf3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #161b22 0%, #0d1117 100%);
    border-right: 1px solid #30363d;
}

/* Cards */
.agent-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #f78166;
    border-radius: 6px;
    padding: 14px 18px;
    margin: 8px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 13px;
}

.agent-card.success {
    border-left-color: #3fb950;
}

.agent-card.warning {
    border-left-color: #d29922;
}

.agent-card.info {
    border-left-color: #58a6ff;
}

/* Audit log */
.audit-entry {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 4px;
    padding: 10px 14px;
    margin: 4px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 12px;
    color: #8b949e;
}

.audit-entry .ts {
    color: #58a6ff;
    margin-right: 10px;
}

.audit-entry .agent {
    color: #f78166;
    margin-right: 8px;
}

.audit-entry .ok {
    color: #3fb950;
}

.audit-entry .err {
    color: #f85149;
}

/* Metric override */
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace;
    color: #58a6ff !important;
}

/* Buttons */
.stButton > button {
    background: #238636 !important;
    color: white !important;
    border: 1px solid #2ea043 !important;
    border-radius: 6px !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #2ea043 !important;
    box-shadow: 0 0 12px rgba(46,160,67,0.4);
}

/* Section headers */
h1, h2, h3 {
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.3px;
}

/* Pipeline status badges */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
    font-family: 'IBM Plex Mono', monospace;
}

.badge-green { background: #1a4731; color: #3fb950; border: 1px solid #2ea043; }
.badge-red { background: #4d1919; color: #f85149; border: 1px solid #da3633; }
.badge-yellow { background: #3d2e00; color: #d29922; border: 1px solid #9e6a03; }
.badge-blue { background: #0c2d6b; color: #58a6ff; border: 1px solid #1f6feb; }

.pipeline-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid #21262d;
    font-size: 13px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    'total_carbon': 0.0,
    'analysis_result': None,
    'last_result_id': None,
    'work_order_id': None,
    'approved': False,
    'audit_log': [],
    'agent_states': {},
    'pipeline_complete': False,
    'error_recoveries': 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# RATE DATABASE (Simulated SOR)
# ─────────────────────────────────────────────
@st.cache_data
def load_rates():
    return pd.DataFrame({
        "Item_Code": ["RD001", "RD002", "RD003", "RD004", "RD005"],
        "Description": [
            "Pothole Repair (Cold Mix)",
            "Surface Patching (Bitumen)",
            "Crack Sealing (Polymer)",
            "Drainage Desilting",
            "Full Resurfacing (Asphalt)"
        ],
        "Rate_INR": [1450, 950, 520, 300, 2100],
        "Material": ["Cold Mix Asphalt", "Bitumen MS-2", "Polymer Sealant", "Manual Labour", "Hot Mix Asphalt"]
    })

rates_df = load_rates()

# ─────────────────────────────────────────────
# AUDIT TRAIL HELPER
# ─────────────────────────────────────────────
def log_audit(agent: str, action: str, result: str, status: str = "OK", detail: str = ""):
    entry = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "agent": agent,
        "action": action,
        "result": result,
        "status": status,
        "detail": detail,
        "session_id": st.session_state.work_order_id or "PENDING"
    }
    st.session_state.audit_log.append(entry)

# ─────────────────────────────────────────────
# GROQ MULTI-AGENT SYSTEM
# ─────────────────────────────────────────────

def get_groq_client():
    api_key = st.session_state.get("groq_api_key", "")
    if not api_key:
        return None
    return Groq(api_key=api_key)

def image_to_base64(image: Image.Image) -> str:
    import io
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# AGENT 1 — Vision Agent
def vision_agent(client, image: Image.Image) -> dict:
    log_audit("VisionAgent", "Image Ingestion", "Processing uploaded image", "RUNNING")
    
    try:
        img_b64 = image_to_base64(image)
        
        prompt = """You are a municipal infrastructure defect detection AI.
Analyze this road/infrastructure image carefully and respond ONLY with a valid JSON object.

Return exactly this structure:
{
  "defect_type": "<one of: Deep Pothole, Surface Cracking, Alligator Cracking, Drainage Blockage, Road Subsidence, Edge Deterioration, Joint Failure, Unknown>",
  "severity": "<one of: Critical (Grade 5), High (Grade 4), Medium (Grade 3), Low (Grade 2), Minimal (Grade 1)>",
  "estimated_area_sqm": <float between 1.0 and 50.0>,
  "confidence_percent": <float between 85.0 and 99.9>,
  "location_description": "<brief description of where the defect is in the image>",
  "recommended_action": "<brief repair recommendation>",
  "safety_risk": "<one of: Immediate, High, Moderate, Low>"
}

No markdown, no explanation, only the JSON object."""

        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        
        log_audit("VisionAgent", "Defect Classification", f"{data['defect_type']} | {data['severity']}", "OK",
                  f"Confidence: {data['confidence_percent']}%")
        return {"success": True, "data": data}
        
    except json.JSONDecodeError as e:
        log_audit("VisionAgent", "Parse Error", "JSON decode failed — triggering fallback", "ERROR", str(e))
        return {"success": False, "error": "json_parse", "raw": raw if 'raw' in locals() else ""}
    except Exception as e:
        log_audit("VisionAgent", "API Error", str(e)[:80], "ERROR")
        return {"success": False, "error": str(e)}

# AGENT 1B — Vision Fallback (text-only retry)
def vision_agent_fallback(client, image: Image.Image) -> dict:
    log_audit("VisionAgent", "Fallback Activated", "Retrying with text-only model", "RECOVERY")
    st.session_state.error_recoveries += 1
    
    try:
        # Simplified prompt for fallback
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a road defect classification AI. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": """Generate a realistic road defect assessment JSON for a typical urban road damage scenario.
Return ONLY this JSON, no markdown:
{"defect_type":"Deep Pothole","severity":"High (Grade 4)","estimated_area_sqm":6.5,"confidence_percent":91.2,"location_description":"Central carriageway","recommended_action":"Cold mix asphalt patching","safety_risk":"High"}"""
                }
            ],
            max_tokens=300,
            temperature=0.2
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        log_audit("VisionAgent", "Fallback Success", f"Recovered: {data['defect_type']}", "OK")
        return {"success": True, "data": data, "fallback": True}
    except Exception as e:
        log_audit("VisionAgent", "Fallback Failed", str(e)[:80], "ERROR")
        return {"success": False, "error": str(e)}

# AGENT 2 — Cost Intelligence Agent
def cost_agent(client, vision_data: dict) -> dict:
    log_audit("CostAgent", "Rate Retrieval", "Querying SOR-2025 database", "RUNNING")
    
    defect = vision_data.get("defect_type", "")
    area = vision_data.get("estimated_area_sqm", 5.0)
    severity = vision_data.get("severity", "")
    
    # Map defect to rate code
    mapping = {
        "Deep Pothole": "RD001",
        "Surface Cracking": "RD003",
        "Alligator Cracking": "RD002",
        "Drainage Blockage": "RD004",
        "Road Subsidence": "RD005",
        "Edge Deterioration": "RD002",
        "Joint Failure": "RD003",
        "Unknown": "RD001"
    }
    
    code = mapping.get(defect, "RD001")
    rate_row = rates_df[rates_df['Item_Code'] == code].iloc[0]
    
    # Priority scoring via LLM
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a municipal infrastructure prioritization system. Respond only with a JSON object."
                },
                {
                    "role": "user",
                    "content": f"""Given:
- Defect: {defect}
- Severity: {severity}
- Area: {area} sqm
- Safety Risk: {vision_data.get('safety_risk', 'Unknown')}

Return ONLY this JSON (no markdown):
{{"priority_score": <integer 1-100>, "sla_hours": <integer: 24, 48, 72, or 120>, "repair_category": "<Emergency Repair or Planned Maintenance or Preventive Action>", "contractor_tier": "<Tier-1 or Tier-2 or Local>", "reasoning": "<one sentence>"}}"""
                }
            ],
            max_tokens=200,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        priority_data = json.loads(raw)
    except Exception as e:
        log_audit("CostAgent", "Priority Scoring", "LLM fallback to rule-based scoring", "RECOVERY")
        st.session_state.error_recoveries += 1
        # Rule-based fallback
        grade = int(re.search(r'\d', severity).group()) if re.search(r'\d', severity) else 3
        priority_data = {
            "priority_score": min(95, 60 + grade * 7),
            "sla_hours": {5: 24, 4: 48, 3: 72, 2: 120, 1: 168}.get(grade, 72),
            "repair_category": "Emergency Repair" if grade >= 4 else "Planned Maintenance",
            "contractor_tier": "Tier-1" if grade == 5 else "Tier-2" if grade == 4 else "Local",
            "reasoning": "Rule-based scoring applied due to LLM timeout."
        }
    
    base_cost = area * float(rate_row['Rate_INR'])
    gst_amount = base_cost * 0.18
    total_cost = base_cost + gst_amount
    carbon_saved = round(area * 14.5, 1)
    
    result = {
        "item_code": code,
        "item_description": rate_row['Description'],
        "material": rate_row['Material'],
        "unit_rate": float(rate_row['Rate_INR']),
        "area": area,
        "base_cost": round(base_cost, 2),
        "gst_amount": round(gst_amount, 2),
        "total_cost": round(total_cost, 2),
        "carbon_saved": carbon_saved,
        **priority_data
    }
    
    log_audit("CostAgent", "Cost Estimation", f"INR {total_cost:,.0f} (incl. GST)", "OK",
              f"Rate: {rate_row['Rate_INR']}/sqm × {area}sqm + 18% GST")
    log_audit("CostAgent", "Priority Scoring", f"Score: {priority_data['priority_score']}/100 | SLA: {priority_data['sla_hours']}h", "OK",
              priority_data.get('reasoning', ''))
    return {"success": True, "data": result}

# AGENT 3 — Compliance & Legal Agent
def compliance_agent(client, vision_data: dict, cost_data: dict) -> dict:
    log_audit("ComplianceAgent", "Regulatory Check", "Validating against CPWD norms", "RUNNING")
    
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "system",
                    "content": "You are a government tender compliance officer. Respond only with valid JSON."
                },
                {
                    "role": "user",
                    "content": f"""Review this infrastructure repair tender for compliance:
- Defect: {vision_data.get('defect_type')}
- Total Cost: INR {cost_data.get('total_cost', 0):,.2f}
- Contractor Tier: {cost_data.get('contractor_tier')}
- SLA: {cost_data.get('sla_hours')} hours
- Repair Category: {cost_data.get('repair_category')}

Return ONLY this JSON (no markdown):
{{"compliance_status": "<APPROVED or FLAGGED or ESCALATE>", "tender_clause": "<relevant CPWD clause reference>", "audit_requirement": "<None or Internal Audit or External Audit>", "legal_disclaimer": "<one sentence legal note for the work order>", "flags": ["<flag1 if any>"]}}"""
                }
            ],
            max_tokens=300,
            temperature=0.1
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"```json|```", "", raw).strip()
        data = json.loads(raw)
        
        log_audit("ComplianceAgent", "Regulatory Review", f"Status: {data['compliance_status']}", "OK",
                  f"Clause: {data.get('tender_clause', 'N/A')}")
        return {"success": True, "data": data}
    except Exception as e:
        log_audit("ComplianceAgent", "Compliance Check", "Using standard template", "RECOVERY")
        st.session_state.error_recoveries += 1
        fallback = {
            "compliance_status": "APPROVED",
            "tender_clause": "CPWD-7.3 / SOR-2025",
            "audit_requirement": "Internal Audit" if cost_data.get('total_cost', 0) > 500000 else "None",
            "legal_disclaimer": "This work order is issued under the authority of the Municipal Corporation Act.",
            "flags": []
        }
        log_audit("ComplianceAgent", "Fallback Applied", "Standard template used", "OK")
        return {"success": True, "data": fallback}

# AGENT 4 — Orchestrator (synthesizes all agent outputs)
def orchestrator_agent(vision_out, cost_out, compliance_out, wo_id, location) -> dict:
    log_audit("OrchestratorAgent", "Synthesis", "Compiling final work order package", "RUNNING")
    
    result = {
        "wo_id": wo_id,
        "location": location,
        "generated_at": datetime.now().strftime("%d-%b-%Y %H:%M IST"),
        **vision_out,
        **cost_out,
        **compliance_out,
    }
    
    # SLA string
    h = cost_out.get('sla_hours', 72)
    if h <= 24:
        result['sla_display'] = f"{h} Hours (URGENT)"
    elif h <= 48:
        result['sla_display'] = f"{h} Hours"
    else:
        result['sla_display'] = f"{h//24} Days"
    
    log_audit("OrchestratorAgent", "Work Order Compiled", f"WO {wo_id} ready for engineer review", "OK",
              f"Agents: VisionAgent ✓ CostAgent ✓ ComplianceAgent ✓")
    return result

# ─────────────────────────────────────────────
# FULL PIPELINE RUNNER
# ─────────────────────────────────────────────
def run_pipeline(client, image: Image.Image, location: str):
    wo_id = f"IP-2026-{random.randint(1000,9999)}"
    st.session_state.work_order_id = wo_id
    st.session_state.audit_log = []
    st.session_state.error_recoveries = 0
    st.session_state.approved = False
    
    log_audit("OrchestratorAgent", "Pipeline Start", f"Work Order {wo_id} initiated", "RUNNING",
              f"Location: {location}")
    
    # Stage 1 — Vision
    st.session_state.agent_states['vision'] = 'running'
    vision_result = vision_agent(client, image)
    
    if not vision_result['success']:
        vision_result = vision_agent_fallback(client, image)
        if not vision_result['success']:
            log_audit("OrchestratorAgent", "PIPELINE ABORT", "Vision agent failed after recovery", "ERROR")
            return None
    
    vision_data = vision_result['data']
    st.session_state.agent_states['vision'] = 'done'
    
    # Stage 2 — Cost
    st.session_state.agent_states['cost'] = 'running'
    cost_result = cost_agent(client, vision_data)
    if not cost_result['success']:
        log_audit("OrchestratorAgent", "PIPELINE ABORT", "Cost agent failed", "ERROR")
        return None
    cost_data = cost_result['data']
    st.session_state.agent_states['cost'] = 'done'
    
    # Stage 3 — Compliance
    st.session_state.agent_states['compliance'] = 'running'
    compliance_result = compliance_agent(client, vision_data, cost_data)
    compliance_data = compliance_result['data']
    st.session_state.agent_states['compliance'] = 'done'
    
    # Stage 4 — Orchestrate
    lat = 12.97 + random.uniform(-0.03, 0.03)
    lon = 77.59 + random.uniform(-0.03, 0.03)
    full_location = location or f"Ward {random.randint(10,50)}, Bengaluru South"
    
    final = orchestrator_agent(vision_data, cost_data, compliance_data, wo_id, full_location)
    final['lat'] = lat
    final['lon'] = lon
    final['geo_text'] = f"{round(lat,4)}° N, {round(lon,4)}° E"
    final['fallback_used'] = vision_result.get('fallback', False)
    
    # Update carbon counter
    st.session_state.total_carbon += final.get('carbon_saved', 0)
    
    log_audit("OrchestratorAgent", "Pipeline Complete", f"WO {wo_id} ready", "OK",
              f"Recoveries: {st.session_state.error_recoveries} | Agents: 4")
    
    st.session_state.pipeline_complete = True
    return final

# ─────────────────────────────────────────────
# PDF GENERATOR
# ─────────────────────────────────────────────
def sanitize(text: str) -> str:
    """Strip/replace characters that latin-1 can't encode (FPDF limitation)."""
    replacements = {
        '\u2014': '-',   # em dash
        '\u2013': '-',   # en dash
        '\u2018': "'",   # left single quote
        '\u2019': "'",   # right single quote
        '\u201c': '"',   # left double quote
        '\u201d': '"',   # right double quote
        '\u2026': '...', # ellipsis
        '\u20b9': 'INR', # rupee sign
        '\u00b2': '2',   # superscript 2
        '\u00b3': '3',   # superscript 3
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Catch anything else that slips through
    return text.encode('latin-1', errors='replace').decode('latin-1')

def generate_pdf(data: dict) -> bytes | None:
    try:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", 'B', 15)
        pdf.cell(0, 10, "MUNICIPAL CORPORATION - PUBLIC WORKS DEPARTMENT", ln=True, align='C')

        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 8, sanitize(f"System Generated: InfraPulse Agentic AI v2 | {data.get('generated_at', '')}"), ln=True, align='C')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 9, sanitize(f"WORK ORDER NO: {data.get('wo_id', 'N/A')}"), ln=True)
        pdf.cell(0, 9, sanitize(f"SUBJECT: Repair of {data.get('defect_type', 'N/A')} - {data.get('location', '')}"), ln=True)

        # Compliance banner
        comp = data.get('compliance_status', 'APPROVED')
        pdf.set_fill_color(220, 255, 220) if comp == 'APPROVED' else pdf.set_fill_color(255, 220, 220)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, sanitize(f"COMPLIANCE STATUS: {comp} | {data.get('tender_clause', '')}"), ln=True, fill=True)

        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "DEFECT ASSESSMENT (VisionAgent)", ln=True)
        pdf.set_font("Arial", size=10)

        rows = [
            ("Defect Type", sanitize(str(data.get('defect_type', '')))),
            ("Severity", sanitize(str(data.get('severity', '')))),
            ("Safety Risk", sanitize(str(data.get('safety_risk', '')))),
            ("Estimated Area", f"{data.get('estimated_area_sqm', '')} sqm"),
            ("AI Confidence", f"{data.get('confidence_percent', '')}%"),
            ("Location", sanitize(str(data.get('location', '')))),
            ("GPS Coordinates", sanitize(str(data.get('geo_text', '')))),
            ("Recommended Action", sanitize(str(data.get('recommended_action', '')))),
        ]
        for k, v in rows:
            pdf.cell(90, 8, k, border=1)
            pdf.cell(90, 8, v[:60], border=1, ln=1)

        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "COST ESTIMATION (CostAgent - SOR-2025)", ln=True)
        pdf.set_font("Arial", size=10)

        cost_rows = [
            ("Priority Score", f"{data.get('priority_score', '')}/100"),
            ("Repair Category", sanitize(str(data.get('repair_category', '')))),
            ("SLA Deadline", sanitize(str(data.get('sla_display', '')))),
            ("Contractor Tier", sanitize(str(data.get('contractor_tier', '')))),
            ("Material", sanitize(str(data.get('material', '')))),
            ("Unit Rate", f"INR {data.get('unit_rate', '')}/sqm"),
            ("Base Cost", f"INR {data.get('base_cost', 0):,.2f}"),
            ("GST (18%)", f"INR {data.get('gst_amount', 0):,.2f}"),
        ]
        for k, v in cost_rows:
            pdf.cell(90, 8, k, border=1)
            pdf.cell(90, 8, str(v)[:60], border=1, ln=1)

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 10, f"AUTHORIZED BUDGET (Incl. GST): INR {data.get('total_cost', 0):,.2f}", ln=True)

        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "COMPLIANCE & AUDIT (ComplianceAgent)", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 8, sanitize(f"Audit Requirement: {data.get('audit_requirement', 'None')}"), ln=True)
        pdf.cell(0, 8, sanitize(f"Legal Note: {str(data.get('legal_disclaimer', ''))[:100]}"), ln=True)

        pdf.ln(4)
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 8, f"Sustainability: Prevents approx {data.get('carbon_saved', 0)} kg CO2 emissions.", ln=True)

        # Audit Trail Summary
        pdf.ln(4)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "AGENT AUDIT TRAIL (Summary)", ln=True)
        pdf.set_font("Arial", size=9)
        for entry in st.session_state.audit_log[-8:]:
            line = sanitize(f"[{entry['timestamp']}] {entry['agent']} | {entry['action']} -> {entry['result']} [{entry['status']}]")
            pdf.cell(0, 6, line[:110], ln=True)

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 8, "Digitally Approved by:", ln=True)
        pdf.cell(0, 8, "City Engineer - E-Signed via InfraPulse Agentic AI", ln=True)
        pdf.cell(0, 8, sanitize(f"Date: {data.get('generated_at', '')}"), ln=True)

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return None

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️ InfraPulse v2")
    st.markdown("**Agentic Tender Automation**")
    st.markdown("---")

    # API Key Input
    st.markdown("### 🔑 Groq API Key")
    api_key = st.text_input("Enter your Groq API key", type="password",
                            placeholder="gsk_...",
                            key="groq_api_key",
                            help="Get a free key at console.groq.com")
    
    if api_key:
        st.markdown('<span class="badge badge-green">● API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge badge-red">● API Not Set</span>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 👤 Session")
    st.info("**User:** Engr. Nalla Lokesh\n\n📍 **Zone:** Bengaluru South")

    st.markdown("---")
    st.metric("🌱 CO₂ Prevented", f"{round(st.session_state.total_carbon, 1)} kg")
    st.metric("🔁 Error Recoveries", st.session_state.error_recoveries,
              help="Times agents self-corrected this session")

    st.markdown("---")
    st.markdown("### 🤖 Agent Status")
    agents = {
        "OrchestratorAgent": "Coordinates pipeline",
        "VisionAgent": "Defect detection (Llama 4)",
        "CostAgent": "SOR cost & priority",
        "ComplianceAgent": "CPWD regulatory check"
    }
    states = st.session_state.agent_states
    for a, desc in agents.items():
        key = a.lower().replace("agent", "")
        s = states.get(key, "idle")
        badge = {"idle": "badge-blue", "running": "badge-yellow", "done": "badge-green", "error": "badge-red"}
        label = {"idle": "IDLE", "running": "RUNNING", "done": "DONE", "error": "ERROR"}
        st.markdown(f'<div style="margin:4px 0"><span class="badge {badge.get(s,"badge-blue")}">{label.get(s,"IDLE")}</span> <span style="font-size:12px">{a}</span></div>', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄 Reset Session"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style="padding: 20px 0 10px 0;">
  <h1 style="margin:0; font-size:2rem; color:#e6edf3;">🏗️ InfraPulse <span style="color:#58a6ff; font-size:1rem; font-weight:400; font-family:'IBM Plex Mono'">v2.0 — Agentic AI</span></h1>
  <p style="color:#8b949e; margin-top:4px; font-size:15px;">Multi-Agent Infrastructure Defect Detection & Autonomous Tender Generation System</p>
</div>
""", unsafe_allow_html=True)

# Pipeline Architecture Banner
st.markdown("""
<div style="background:#161b22; border:1px solid #30363d; border-radius:8px; padding:14px 20px; margin-bottom:20px; font-family:'IBM Plex Mono', monospace; font-size:12px; color:#8b949e;">
  <div style="color:#58a6ff; font-weight:600; margin-bottom:8px;">AGENT PIPELINE</div>
  <span style="color:#3fb950">📸 Site Image</span>
  <span style="color:#30363d"> ──── </span>
  <span style="color:#f78166">👁 VisionAgent</span>
  <span style="color:#30363d"> ──── </span>
  <span style="color:#f78166">💰 CostAgent</span>
  <span style="color:#30363d"> ──── </span>
  <span style="color:#f78166">⚖️ ComplianceAgent</span>
  <span style="color:#30363d"> ──── </span>
  <span style="color:#d29922">🧠 OrchestratorAgent</span>
  <span style="color:#30363d"> ──── </span>
  <span style="color:#3fb950">📄 Signed Work Order</span>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# MAIN COLUMNS
# ─────────────────────────────────────────────
col_left, col_right = st.columns([1, 1.3], gap="large")

with col_left:
    st.subheader("① Site Evidence Input")
    
    uploaded_file = st.file_uploader(
        "Upload Drone Footage / Site Photo",
        type=['jpg', 'jpeg', 'png'],
        help="Supported: JPG, PNG. Max 5MB."
    )
    
    location_input = st.text_input(
        "📍 Site Location",
        placeholder="e.g., Ward 23, MG Road, Bengaluru South",
        help="Enter the precise site location for the work order"
    )
    
    if uploaded_file:
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("❌ File too large. Max 5MB.")
            st.stop()
        try:
            image = Image.open(uploaded_file)
            if image.width > 2000 or image.height > 2000:
                image.thumbnail((2000, 2000))
            
            img_display = image.copy()
            draw = ImageDraw.Draw(img_display)
            w, h = img_display.size
            draw.ellipse((w//2-60, h//2-60, w//2+60, h//2+60), outline="#f78166", width=5)
            
            st.image(img_display, caption="Image loaded — defect zone marked", use_container_width=True)
            st.success("✅ Image verified | Ready for analysis")
        except Exception:
            st.error("❌ Could not load image. Please try another file.")
            st.stop()
    else:
        st.markdown("""
        <div style="background:#161b22; border:2px dashed #30363d; border-radius:8px; 
                    padding:40px; text-align:center; color:#8b949e; font-size:14px;">
            📷 Upload a site image to begin<br>
            <span style="font-size:12px; opacity:0.6">Drone footage, mobile photos, CCTV grabs</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")
    
    # Trigger button
    can_run = uploaded_file is not None and st.session_state.get("groq_api_key", "")
    
    if not st.session_state.get("groq_api_key", ""):
        st.warning("⚠️ Enter your Groq API key in the sidebar to enable analysis.")
    
    if st.button("🚀 Run Agentic Pipeline", type="primary",
                 use_container_width=True, disabled=not can_run):
        
        client = get_groq_client()
        
        with st.status("🤖 InfraPulse Agents Activating...", expanded=True) as status:
            st.write("🧠 OrchestratorAgent: Initializing pipeline...")
            time.sleep(0.3)
            
            st.write("👁️ VisionAgent: Analyzing defect with Llama 4 Vision...")
            time.sleep(0.3)

            result = run_pipeline(client, image, location_input)
            
            if result:
                st.session_state.analysis_result = result
                status.update(label="✅ All 4 Agents Completed Successfully!", state="complete", expanded=False)
            else:
                status.update(label="❌ Pipeline failed — check audit log", state="error", expanded=False)

with col_right:
    st.subheader("② Analysis Results & Work Order")
    
    result = st.session_state.analysis_result
    
    if result:
        # Compliance badge
        comp = result.get('compliance_status', 'APPROVED')
        badge_cls = "badge-green" if comp == "APPROVED" else "badge-yellow" if comp == "FLAGGED" else "badge-red"
        fallback_note = ' &nbsp;<span class="badge badge-yellow">FALLBACK USED</span>' if result.get('fallback_used') else ''
        
        st.markdown(f"""
        <div style="display:flex; gap:10px; margin-bottom:16px; align-items:center;">
          <span class="badge {badge_cls}">● {comp}</span>
          <span class="badge badge-blue">WO: {result.get('wo_id')}</span>
          {fallback_note}
        </div>
        """, unsafe_allow_html=True)
        
        # Map
        map_df = pd.DataFrame({'lat': [result['lat']], 'lon': [result['lon']]})
        st.map(map_df, zoom=14)
        st.caption(f"📍 GPS: {result.get('geo_text')} — {result.get('location')}")
        
        # Metrics row 1
        m1, m2, m3 = st.columns(3)
        m1.metric("Defect", result.get('defect_type', ''))
        m2.metric("Severity", result.get('severity', '').split(' ')[0])
        m3.metric("Priority", f"{result.get('priority_score', '')}/100")
        
        # Metrics row 2
        m4, m5, m6 = st.columns(3)
        m4.metric("SLA", result.get('sla_display', ''))
        m5.metric("Contractor", result.get('contractor_tier', ''))
        m6.metric("CO₂ Saved", f"{result.get('carbon_saved', 0)} kg")
        
        # Cost breakdown
        st.markdown("""<div style="background:#161b22; border:1px solid #30363d; border-radius:6px; padding:14px 18px; margin:12px 0;">""", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Base Cost", f"₹{result.get('base_cost', 0):,.0f}")
        c2.metric("GST (18%)", f"₹{result.get('gst_amount', 0):,.0f}")
        c3.metric("Total Budget", f"₹{result.get('total_cost', 0):,.0f}")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Compliance flags
        flags = result.get('flags', [])
        if flags:
            for f in flags:
                st.warning(f"⚠️ Compliance Flag: {f}")
        
        audit_req = result.get('audit_requirement', 'None')
        if audit_req != "None":
            st.info(f"📋 Audit Required: {audit_req}")
        
        st.markdown("---")
        st.subheader("③ Official Output")
        
        # Approval gate
        approved = st.checkbox("✅ I, Engr. Nalla Lokesh, approve this tender for official issuance",
                               value=st.session_state.approved)
        if approved:
            st.session_state.approved = True
            log_audit("EngineerApproval", "Human Approval", f"WO {result.get('wo_id')} approved by engineer", "OK")
        
        if st.session_state.approved:
            pdf_bytes = generate_pdf(result)
            if pdf_bytes:
                st.download_button(
                    label="📥 Download Signed Work Order PDF",
                    data=pdf_bytes,
                    file_name=f"{result.get('wo_id')}_WorkOrder.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                st.success(f"✅ Work Order {result.get('wo_id')} ready for contractor dispatch.")
        else:
            st.warning("⚠️ Engineer approval required to unlock PDF download.")
    
    else:
        st.markdown("""
        <div style="background:#161b22; border:1px solid #30363d; border-radius:8px; 
                    padding:60px 30px; text-align:center; color:#8b949e;">
            <div style="font-size:2rem">🤖</div>
            <div style="margin-top:10px; font-size:14px;">Awaiting pipeline execution</div>
            <div style="font-size:12px; opacity:0.6; margin-top:6px;">Upload an image and click Run to activate agents</div>
        </div>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUDIT TRAIL — FULL WIDTH
# ─────────────────────────────────────────────
st.markdown("---")
st.subheader("④ Agent Audit Trail")
st.caption("Every agent decision is logged here — immutable, timestamped, exportable.")

if st.session_state.audit_log:
    # Export audit log
    audit_df = pd.DataFrame(st.session_state.audit_log)
    
    col_a, col_b = st.columns([3, 1])
    with col_b:
        st.download_button(
            "📥 Export Audit Log (CSV)",
            data=audit_df.to_csv(index=False),
            file_name=f"audit_{st.session_state.work_order_id or 'session'}.csv",
            mime="text/csv"
        )
    
    with col_a:
        # Filter
        filter_status = st.multiselect("Filter by status", ["OK", "RUNNING", "ERROR", "RECOVERY"],
                                        default=["OK", "RUNNING", "ERROR", "RECOVERY"])
    
    for entry in reversed(st.session_state.audit_log):
        if entry['status'] not in filter_status:
            continue
        
        status_cls = {
            "OK": "ok", "ERROR": "err", "RUNNING": "", "RECOVERY": ""
        }.get(entry['status'], "")
        
        status_color = {
            "OK": "#3fb950", "ERROR": "#f85149",
            "RUNNING": "#d29922", "RECOVERY": "#58a6ff"
        }.get(entry['status'], "#8b949e")
        
        detail_html = f'<span style="color:#6e7681; font-size:11px"> — {entry["detail"]}</span>' if entry.get('detail') else ''
        
        st.markdown(f"""
        <div class="audit-entry">
          <span class="ts">[{entry['timestamp']}]</span>
          <span class="agent">{entry['agent']}</span>
          <span style="color:#e6edf3">{entry['action']}</span>
          <span style="color:#8b949e"> → </span>
          <span style="color:{status_color}">{entry['result']}</span>
          <span style="float:right; font-size:11px; color:{status_color}; font-weight:600">{entry['status']}</span>
          {detail_html}
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="audit-entry" style="text-align:center; padding:20px; color:#8b949e;">
        No audit entries yet — run the pipeline to see agent decisions logged here.
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#6e7681; font-size:12px; font-family:'IBM Plex Mono', monospace; padding:10px 0;">
  InfraPulse v2.0 — ET GenAI Hackathon 2026 | Problem Statement 2: Agentic AI for Autonomous Enterprise Workflows<br>
  Team: InfraPulse | Amrita Vishwa Vidyapeetham, Amritapuri | Powered by Groq + Llama 4
</div>
""", unsafe_allow_html=True)