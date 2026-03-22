import streamlit as st
import pandas as pd
from fpdf import FPDF
import time
import random
from datetime import datetime
from PIL import Image, ImageDraw
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="InfraPulse | AI Tender Automator",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SESSION STATE INITIALIZATION ---
if 'total_carbon' not in st.session_state:
    st.session_state.total_carbon = 0.0
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None
if 'last_result_id' not in st.session_state:
    st.session_state.last_result_id = None
if 'work_order_id' not in st.session_state:
    st.session_state.work_order_id = None
# New: Approval Lock State
if 'approved' not in st.session_state:
    st.session_state.approved = False

# --- LOAD DATABASE (Simulated RAG) ---
@st.cache_data
def load_rates():
    return pd.DataFrame({
        "Item_Code": ["RD001", "RD002", "RD003", "RD004"],
        "Description": ["Pothole Repair (Cold Mix)", "Surface Patching (Bitumen)", "Crack Sealing (Polymer)", "Drainage Desilting"],
        "Rate_INR": [1450, 950, 520, 300]
    })

rates_df = load_rates()

# --- MOCK AI ENGINE (Dynamic Scenarios) ---
def mock_ai_analysis():
    # Note: Sleep is handled in the UI progress bar now
    
    scenarios = [
        {"defect": "Deep Pothole / Structural Failure", "severity": "Critical (Grade 5)", "material_code": "RD001", "base_area": 5.0, "sla": "24 Hours"},
        {"defect": "Alligator Cracking / Surface Fatigue", "severity": "High (Grade 4)", "material_code": "RD002", "base_area": 11.0, "sla": "48 Hours"},
        {"defect": "Longitudinal Joint Crack", "severity": "Medium (Grade 3)", "material_code": "RD003", "base_area": 3.5, "sla": "5 Days"},
        {"defect": "Stormwater Drain Blockage", "severity": "High (Grade 4)", "material_code": "RD004", "base_area": 8.5, "sla": "48 Hours"}
    ]

    scenario = random.choice(scenarios)
    varied_area = round(scenario["base_area"] * random.uniform(0.85, 1.2), 2)
    varied_conf = f"{round(random.uniform(96.0, 99.8), 1)}%"
    carbon_saved = round(varied_area * 14.5, 1)

    # Priority Score Calculation
    priority_score = random.randint(70, 98)

    # Smart Repair Type Logic
    repair_type = "Emergency Repair" if "Critical" in scenario["severity"] or "High" in scenario["severity"] else "Preventive Maintenance"
    
    # Random Geo-Coords for Map (Bengaluru Area)
    lat = 12.97 + random.uniform(-0.02, 0.02)
    lon = 77.59 + random.uniform(-0.02, 0.02)
    geo_text = f"{round(lat, 4)}° N, {round(lon, 4)}° E"

    return {
        "defect": scenario["defect"],
        "severity": scenario["severity"],
        "area": varied_area,
        "material_code": scenario["material_code"],
        "confidence": varied_conf,
        "location": f"Ward {random.randint(10, 50)}, Bengaluru South",
        "lat": lat,
        "lon": lon,
        "geo_text": geo_text,
        "sla": scenario["sla"],
        "carbon_saved": carbon_saved,
        "priority": priority_score,
        "repair_type": repair_type
    }

# --- PDF GENERATOR ---
def generate_tender_pdf(data, total_cost, unit_rate, wo_id):
    try:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "MUNICIPAL CORPORATION - PUBLIC WORKS DEPT", ln=True, align='C')

        pdf.set_font("Arial", 'I', 10)
        current_date = datetime.now().strftime("%d-%b-%Y | %H:%M IST")
        pdf.cell(0, 10, f"System Generated: InfraPulse AI | Date: {current_date}", ln=True, align='C')
        pdf.line(10, 30, 200, 30)

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"WORK ORDER NO: {wo_id}", ln=True)
        pdf.cell(0, 10, f"SUBJECT: Immediate Repair of {data['defect']}", ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", size=11)

        items = [
            ("Defect Type", data['defect']),
            ("Severity", data['severity']),
            ("Priority Score", f"{data['priority']} / 100"),
            ("Repair Type", data['repair_type']),
            ("Estimated Area", f"{data['area']} sqm"),
            ("Location", data['location']),
            ("Completion Deadline (SLA)", data['sla']),
            ("Material Code", data['material_code'])
        ]

        for key, value in items:
            pdf.cell(90, 10, key, border=1)
            pdf.cell(90, 10, str(value), border=1, ln=1)

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "COST ESTIMATION (As per SOR-2025)", ln=True)

        pdf.set_font("Arial", size=11)
        pdf.cell(0, 8, f"Unit Rate: INR {unit_rate} / sqm", ln=True)
        pdf.cell(0, 8, f"Base Cost: INR {total_cost:,.2f}", ln=True)

        final_amount = total_cost * 1.18
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"TOTAL AUTHORIZED BUDGET (Incl. 18% GST): INR {final_amount:,.2f}", ln=True)

        pdf.ln(5)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(0, 10, f"Sustainability Impact: Prevents approx {data['carbon_saved']} kg of CO2 emissions.", ln=True)

        pdf.ln(15)
        pdf.cell(0, 10, "_________________________", ln=True)
        pdf.cell(0, 10, "City Engineer (E-Signed via InfraPulse)", ln=True)
        
        return pdf
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)
    else:
        st.write("## 🏗️")

    st.title("InfraPulse")
    st.markdown("### Intelligent Tender Automation")
    st.info("👤 **User:** Engr. Nalla Lokesh\n📍 **Zone:** Bengaluru South")

    st.write("---")
    st.metric("🌱 Total CO₂ Saved", f"{round(st.session_state.total_carbon, 1)} kg", help="Cumulative carbon emissions prevented in this session")
    
    st.write("---")
    st.write("### 🕒 Recent Activity")
    st.caption("• WO-982: Pothole approved (10m ago)")
    st.caption("• WO-981: Contractor assigned (1h ago)")
    st.caption("• WO-980: Payment released (2h ago)")

    st.write("---")
    st.success("🟢 AI Inference Engine: Online")
    st.success("🟢 SOR Database: Connected")
    st.warning("⚠️ Prototype Mode — Human approval required")

# --- HEADER ---
st.title("🏗️ InfraPulse Dashboard")
st.markdown('<p style="font-size:20px; color:#555;">Automated Defect Detection & Government Tender Generation System</p>', unsafe_allow_html=True)
st.markdown("---")

# --- MAIN UI ---
col_input, col_process = st.columns([1, 1.2], gap="large")

with col_input:
    st.subheader("1. 📸 Site Evidence Input")
    uploaded_file = st.file_uploader("Upload Drone Footage / Site Image", type=['jpg', 'jpeg', 'png'])

    if uploaded_file:
        if uploaded_file.size > 5 * 1024 * 1024:
            st.error("❌ File too large. Please upload an image under 5 MB.")
            st.stop()
            
        try:
            image = Image.open(uploaded_file)
            
            # Auto-Resize for Safety
            if image.width > 2000 or image.height > 2000:
                image.thumbnail((2000, 2000))

                
            img_display = image.copy()
            draw = ImageDraw.Draw(img_display)
            w, h = img_display.size
            draw.ellipse((w//2-60, h//2-60, w//2+60, h//2+60), outline="#FF0000", width=6)

            st.image(img_display, caption="AI Analysis: Defect Localized", use_container_width=True)
            st.success("✅ Image Quality Verified | Geo-Tag Extracted")
        except Exception as e:
            st.error("❌ Error loading image. Please upload a valid file.")
            st.stop()
    else:
        st.info("Waiting for site input...")

with col_process:
    st.subheader("2. ⚙️ AI Processing Core")

    # Only show button if file uploaded
    if uploaded_file:
        if st.button("🛠️ Initiate Automated Tender Drafting", type="primary", use_container_width=True):

            # Progress Bar Animation
            with st.status("🚀 Initializing InfraPulse Agents...", expanded=True) as status:
                progress = st.progress(0)
                
                st.write("🔍 Vision Agent: Scanning surface...")
                time.sleep(0.8)
                progress.progress(25)
                
                st.write("📐 Geometry Agent: Calculating dimensions...")
                time.sleep(0.8)
                progress.progress(50)
                
                st.write("🏛️ RAG Agent: Fetching SOR rates...")
                time.sleep(0.6)
                progress.progress(75)
                
                st.write("🌱 Sustainability Agent: Computing carbon impact...")
                time.sleep(0.5)
                progress.progress(100)

                result = mock_ai_analysis()
                
                # Prevent Double Counting
                current_id = str(result['defect']) + str(result['area']) + str(time.time())
                
                if st.session_state.last_result_id != current_id:
                    st.session_state.analysis_result = result
                    st.session_state.total_carbon += result['carbon_saved']
                    st.session_state.last_result_id = current_id
                    st.session_state.work_order_id = f"IP-2026-{random.randint(1000, 9999)}"
                    # Reset approval on new analysis
                    st.session_state.approved = False

                status.update(label="✅ Analysis & Drafting Complete!", state="complete", expanded=False)

    # --- DISPLAY RESULTS FROM SESSION STATE ---
    if st.session_state.analysis_result:
        result = st.session_state.analysis_result
        
        st.write("### 📊 Analysis Results")
        
        # Map Visualization
        map_df = pd.DataFrame({'lat': [result['lat']], 'lon': [result['lon']]})
        st.map(map_df, zoom=14)
        # UPGRADE 1: Geo-Caption
        st.caption(f"📍 GPS Coordinates: {result['geo_text']}")

        m1, m2, m3 = st.columns(3)
        m1.metric("Defect Type", result['defect'])
        m2.metric("Severity", result['severity'])
        m3.metric("Priority Score", f"{result['priority']} / 100", help="AI-calculated urgency")

        m4, m5, m6 = st.columns(3)
        m4.metric("SLA Deadline", result['sla'])
        m5.metric("Repair Type", result['repair_type'])
        m6.metric("Carbon Saved", f"{result['carbon_saved']} kg", delta="Sustainability Impact")

        rate_row = rates_df[rates_df['Item_Code'] == result['material_code']]
        unit_rate = rate_row['Rate_INR'].values[0]
        base_cost = result['area'] * unit_rate
        final_ui_amount = base_cost * 1.18

        st.divider()

        # Contractor Routing
        if final_ui_amount < 100000:
            contractor_type = "Local Small Contractor"
        elif final_ui_amount < 500000:
            contractor_type = "Registered Medium Contractor"
        else:
            contractor_type = "Tier-1 Infrastructure Contractor"

        st.metric("Recommended Contractor Category", contractor_type, help="Auto-routing based on tender value threshold")

        if final_ui_amount > 400000:
            st.warning("⚠️ High-Value Tender: Auto-Audit & Transparency Flag Enabled")

        st.subheader("3. 📄 Official Output")
        st.success(f"💰 Authorized Budget (Incl. GST): INR {final_ui_amount:,.2f}")

        # PDF Generation
        wo_id = st.session_state.work_order_id
        pdf_obj = generate_tender_pdf(result, base_cost, unit_rate, wo_id)
        
        if pdf_obj:
            pdf_bytes = pdf_obj.output(dest='S').encode('latin-1')
            
            # UPGRADE 2: Locked Approval Logic
            approved = st.checkbox("✅ I approve this tender estimate for official issuance", value=st.session_state.approved)

            if approved:
                st.session_state.approved = True
            
            if st.session_state.approved:
                st.download_button(
                    label="📥 Download Signed Work Order (PDF)",
                    data=pdf_bytes,
                    file_name=f"{wo_id}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("⚠️ Engineer approval required to unlock download.")
    
    # Reset Button
    st.divider()
    if st.button("🔄 Reset Analysis & Start New Case"):
        st.session_state.analysis_result = None
        st.session_state.last_result_id = None
        st.session_state.work_order_id = None
        st.session_state.approved = False
        st.session_state.total_carbon = 0.0
        st.rerun()