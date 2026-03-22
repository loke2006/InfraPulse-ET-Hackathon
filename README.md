# 🏗️ InfraPulse – AI Tender Automator

## 🚀 Project Overview

InfraPulse is an AI-powered Smart City prototype that automates the **entire municipal tender workflow** for road and infrastructure defects.

Instead of waiting days for manual inspection, estimation, and tender drafting, InfraPulse:

* Detects road defects from city camera / drone images
* Automatically determines severity, SLA, and repair type
* Fetches government Schedule of Rates (SOR)
* Estimates cost with GST
* Calculates sustainability impact (carbon saved)
* Generates an **official, signed Work Order PDF** in seconds

This system demonstrates how **AI + Governance + Sustainability** can reduce execution lag in city infrastructure maintenance.

---

## 🎯 Key Features

### 🔍 Automated Defect Analysis

* Simulates AI-based detection of road defects
* Assigns severity level and priority score
* Classifies repair type (Emergency / Preventive)

### 📍 Smart Location Mapping

* Displays GPS-based defect location on city map
* Simulates camera / drone metadata mapping

### 🏛️ Government-Grade Tender Automation

* Fetches rates from simulated SOR database
* Calculates base cost + GST automatically
* Auto-routes contractor category based on tender value

### 🌱 Sustainability Intelligence

* Computes carbon emissions prevented
* Tracks cumulative carbon savings per session

### 👤 Human-in-the-Loop Governance

* Mandatory approval before tender download
* Audit warning for high-value tenders
* Locked approval workflow

### 📄 Official Output

* Auto-generates a signed Work Order PDF
* Unique Work Order ID for every case

---

## 🖥️ Tech Stack

* **Frontend & UI**: Streamlit
* **Data Handling**: Pandas
* **PDF Generation**: FPDF
* **Image Processing**: Pillow (PIL)
* **Visualization**: Streamlit Maps
* **Language**: Python 3.9+

---

## ⚙️ Installation & Setup

### 1️⃣ Create Virtual Environment (Recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Run the Application

```bash
streamlit run app.py
```

The app will open automatically in your browser at:

```
http://localhost:8501
```

---

## 🧭 How the System Works (Workflow)

1. Upload city camera / drone image
2. System validates file and extracts metadata
3. AI agents simulate defect detection
4. Priority, SLA, and repair type are assigned
5. Rates fetched from SOR database
6. Cost + GST calculated automatically
7. Sustainability impact computed
8. Engineer approves tender
9. Official Work Order PDF is generated

---

## 🏙️ Real-World Architecture (For Jury Explanation)

In production deployment:

* Each city camera is registered in a **GIS Camera Registry**
* Camera ID maps to:

  * Ward
  * Road
  * Latitude & Longitude

When an image arrives:

```
Camera ID → GIS Database → Location + Ward Auto-Fetched
```

For drones and mobile apps:

```
Image EXIF Metadata → GPS Coordinates Extracted Automatically
```

No manual location input required.

---

## ⚠️ Prototype Disclaimer

This is a **hackathon prototype** demonstrating:

* Workflow automation
* Governance logic
* Sustainability intelligence
* Human-in-the-loop approval

Actual AI models, camera APIs, and government databases are simulated for demonstration purposes.

---

## 🏆 Hackathon Highlights

* End-to-end automated tender workflow
* Governance-first design (approval + audit flags)
* Sustainability-aware cost optimization
* Realistic city deployment architecture

---

## 👤 Author

**Lokesh Nalla**
Smart City | AI & Systems Engineering

---

