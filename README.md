# 🐘 Wild Shield Karnataka
## Human–Wildlife Conflict Prevention System
### AI-Powered Multi-Agent Platform | IBM Granite · IBM Cloud · Streamlit

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28%2B-red)
![IBM Granite](https://img.shields.io/badge/IBM%20Granite-LLM-0062FF)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)
![Tests](https://img.shields.io/badge/Tests-143%2F143%20passing-brightgreen)
![License](https://img.shields.io/badge/License-Hackathon%20Demo-lightgrey)

---

> ⚠️ **Data Disclaimer:** This application uses **synthetic demonstration data** for hackathon purposes.
> All incidents are labeled `is_synthetic = TRUE`. No real wildlife locations are exposed.
> This system does **not** claim real-time wildlife tracking.

---

## 📋 Project Overview

**Wild Shield Karnataka** is an AI-powered human–wildlife conflict prevention platform for villages near Karnataka's forests. Two independent AI agents — powered by IBM Granite LLMs — work together to:

1. **Analyse historical wildlife incident data** and identify potential conflict hotspots
2. **Generate localized safety advisories** in Kannada and English for communities and forest officials

Built for **Inter-Institute IBM Bob Hackathon with IBM SkillsBuild · Problem Statement #28**
Domain: Wildlife Conservation, Rural Safety & Disaster Prevention

---

## 🏗️ Architecture

```
╔══════════════════════════════════════════════════════╗
║           Streamlit Dashboard (Frontend)             ║
║  Main · Risk Map · Advisories · Incidents · Console  ║
╚══════════════════════╦═══════════════════════════════╝
                       ↓
╔══════════════════════════════════════════════════════╗
║          Orchestrator Layer (Python)                 ║
║   Coordinates Agent 1 → Agent 2 pipeline             ║
╚═══════════╦══════════════════════════╦═══════════════╝
            ↓                          ↓
╔═══════════════════╗      ╔═══════════════════════════╗
║  AGENT 1          ║      ║  AGENT 2                  ║
║  Risk Assessment  ║ ──→  ║  Safety Advisor           ║
║  IBM Watsonx.ai   ║      ║  Replicate API            ║
║  Granite LLM 1    ║      ║  IBM Granite 4.2-8B       ║
║  API Key 1        ║      ║  API Key 2                ║
╚═══════════════════╝      ╚═══════════════════════════╝
            ↓                          ↓
╔══════════════════════════════════════════════════════╗
║               MySQL Database                         ║
║  villages · incidents · assessments · advisories     ║
╚══════════════════════════════════════════════════════╝
```

---

## 🤖 Two AI Agents

### Agent 1 — Risk Assessment Agent
| Property | Value |
|---|---|
| **LLM** | IBM Granite via IBM Watsonx.ai |
| **API Key** | `WATSONX_API_KEY_1` |
| **Model** | `ibm/granite-13b-instruct-v2` |
| **Temperature** | 0.2 (analytical, consistent) |
| **Input** | Historical incidents, village data, species info |
| **Output** | Risk score (0–100), classification (LOW/MEDIUM/HIGH), hotspot list, narrative explanation |

### Agent 2 — Safety Advisor Agent
| Property | Value |
|---|---|
| **LLM** | IBM Granite 4.2-8B via Replicate API |
| **API Key** | `REPLICATE_API_KEY` |
| **Model** | `ibm-granite/granite-4.2-8b` |
| **Temperature** | 0.7 (natural, conversational language) |
| **Input** | Structured risk assessment from Agent 1 |
| **Output** | Kannada safety advisory, English safety advisory, precautionary actions |

### Agent Communication Workflow
```
1. Historical incident data → Agent 1
2. Agent 1 analyses patterns → risk score + classification
3. Agent 1 output (RiskAssessmentResult JSON) → Agent 2
4. Agent 2 generates Kannada + English safety advisories
5. Both outputs stored in MySQL + displayed on dashboard
```

---

## 🛠️ Technology Stack

| Technology | Role |
|---|---|
| **IBM Bob** | AI-assisted development throughout |
| **IBM Granite (Watsonx.ai)** | LLM backbone — Agent 1 risk analysis |
| **IBM Granite 4.2-8B (Replicate)** | LLM backbone — Agent 2 advisory generation |
| **IBM Cloud** | Cloud infrastructure & Watsonx.ai services |
| **Python 3.11+** | Backend, AI agent logic, data processing |
| **Streamlit 1.28+** | Interactive dashboard & deployment |
| **MySQL 8.0+** | Persistent storage for incidents, assessments, advisories |
| **Folium** | Interactive Leaflet.js maps (hotspot visualization) |
| **Plotly** | Charts, trend graphs, species distribution |
| **Pandas** | Data processing and analysis |
| **python-dotenv** | Environment variable management |

---

## 🚀 Local Setup

### Prerequisites
- Python 3.11+
- MySQL 8.0+
- IBM Watsonx.ai account (API Key + Project ID)
- Replicate account (API token)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-team/wildshield-karnataka.git
cd wildshield-karnataka

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and fill in your API keys and DB credentials

# 5. Create the MySQL database
mysql -u root -p -e "CREATE DATABASE wildshield_karnataka CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 6. Create tables and load synthetic demo data
python3 database/models.py
python3 database/seed_data.py

# 7. Run the application
streamlit run app.py
```

### Open in browser
```
http://localhost:8501
```

> **No API keys?** The app works in fallback mode — CSV-based analysis and template advisories are shown. All 5 dashboard pages are fully navigable.

---

## 🌐 Streamlit Cloud Deployment

1. Push to GitHub (`.env` is in `.gitignore`)
2. Connect repository at [streamlit.io/cloud](https://streamlit.io/cloud)
3. Set the main file to `app.py`
4. Add secrets in **App Settings → Secrets**:

```toml
# Paste into Streamlit Cloud Secrets editor
WATSONX_API_KEY_1    = "your_watsonx_api_key"
WATSONX_PROJECT_ID_1 = "your_watsonx_project_id"
WATSONX_MODEL_ID_1   = "ibm/granite-13b-instruct-v2"
WATSONX_URL_1        = "https://us-south.ml.cloud.ibm.com"

REPLICATE_API_KEY    = "your_replicate_api_token"
REPLICATE_MODEL_ID   = "ibm-granite/granite-4.2-8b"

DB_HOST     = "your_cloud_mysql_host"
DB_PORT     = "3306"
DB_NAME     = "wildshield_karnataka"
DB_USER     = "your_db_user"
DB_PASSWORD = "your_db_password"
```

For a managed cloud MySQL, use **PlanetScale**, **Aiven**, or **Railway** (all have free tiers).

---

## 🧪 Running Tests

```bash
# Run all 143 tests
python3 tests/run_all_tests.py

# Run individual test suites
python3 -m pytest tests/test_agent1.py -v     # 41 tests — Agent 1
python3 -m pytest tests/test_agent2.py -v     # 36 tests — Agent 2
python3 -m pytest tests/test_orchestrator.py -v  # 29 tests — Orchestrator
python3 -m pytest tests/test_utils.py -v      # 37 tests — Utilities

# Test live API connections (requires real API keys in .env)
python3 test_connections.py
```

Expected output:
```
✅ Agent 1 — Risk Assessment     41/41
✅ Agent 2 — Safety Advisor      36/36
✅ Orchestrator — Full Pipeline  29/29
✅ Utils — Helper Functions      37/37
TOTAL: 143/143 tests passed (100%)
```

---

## 📁 Project Structure

```
wildshield-karnataka/
├── app.py                         ← Streamlit entry point (6-page routing)
├── requirements.txt               ← All Python dependencies
├── test_connections.py            ← Standalone API connection tester
├── .env.example                   ← Environment variable template
├── .env                           ← Local secrets (gitignored)
├── .gitignore
├── README.md
│
├── config/
│   └── settings.py                ← Typed config loader (Watsonx + Replicate + DB)
│
├── agents/
│   ├── agent1_risk.py             ← Risk Assessment Agent (IBM Watsonx.ai)
│   └── agent2_safety.py           ← Safety Advisor Agent (Replicate / IBM Granite 4.2-8B)
│
├── orchestrator/
│   └── orchestrator.py            ← Two-agent pipeline coordinator
│
├── database/
│   ├── connection.py              ← MySQL connection pool
│   ├── models.py                  ← 5 tables: villages, incidents, assessments, advisories, boundaries
│   └── seed_data.py               ← Loads 45 synthetic incidents for 11 Karnataka villages
│
├── dashboard/
│   ├── main_page.py               ← KPI cards, trend chart, species donut chart
│   ├── risk_page.py               ← Folium hotspot map, village selector, live Agent 1
│   ├── advisory_page.py           ← Kannada + English advisory cards, batch run
│   ├── incident_page.py           ← Filterable incident table with CSV export
│   └── agent_console_page.py      ← Live pipeline console, JSON viewer, architecture
│
├── utils/
│   └── helpers.py                 ← Risk scoring, formatting, validation utilities
│
├── data/synthetic/
│   └── sample_incidents.csv       ← 45 rows, 11 villages, all is_synthetic=TRUE
│
├── assets/
│   └── style.css                  ← Dashboard CSS
│
├── tests/
│   ├── test_agent1.py             ← 41 unit tests
│   ├── test_agent2.py             ← 36 unit tests
│   ├── test_orchestrator.py       ← 29 integration tests
│   ├── test_utils.py              ← 37 utility tests
│   └── run_all_tests.py           ← Unified test runner
│
└── docs/
    ├── architecture.md            ← Mermaid system diagrams
    ├── deployment_guide.md        ← Step-by-step deployment instructions
    ├── judge_qa.md                ← 20 expected judge questions + model answers
    └── demo_script.md             ← Structured 5-minute live demo script
```

---

## 🔒 Security

- API keys stored in `.env` (local) or Streamlit Secrets (production)
- `.env` excluded from version control via `.gitignore`
- No real wildlife locations disclosed
- All synthetic data clearly labeled (`is_synthetic = TRUE`)
- Advisory validation rejects real-time animal location claims

---

## ⚠️ Limitations

- Analyses **historical** incident data only — not real-time tracking
- Risk assessments reflect patterns, not confirmed current threats
- Demo data is synthetic — clearly labeled throughout the UI
- LLM responses may vary; all outputs are validated before display

---

## 👥 Team

Built for the **Inter-Institute IBM Bob Hackathon with IBM SkillsBuild**
Problem Statement #28 · Domain: Wildlife Conservation, Rural Safety & Disaster Prevention

---

## 📄 License

Built for educational and hackathon demonstration purposes only.
