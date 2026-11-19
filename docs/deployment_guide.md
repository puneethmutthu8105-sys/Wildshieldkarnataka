# Wild Shield Karnataka — Deployment Guide

---

## 1. Local Development Setup

### Prerequisites

| Requirement | Version | Check |
|---|---|---|
| Python | 3.11+ | `python3 --version` |
| pip | Latest | `pip3 --version` |
| MySQL | 8.0+ | `mysql --version` |
| Git | Any | `git --version` |

### Step-by-Step Local Setup

```bash
# ── Step 1: Clone the repository ──────────────────────────────────
git clone https://github.com/your-team/wildshield-karnataka.git
cd wildshield-karnataka

# ── Step 2: Create virtual environment ────────────────────────────
python3 -m venv venv
source venv/bin/activate          # macOS / Linux
# venv\Scripts\activate.bat       # Windows CMD
# venv\Scripts\Activate.ps1       # Windows PowerShell

# ── Step 3: Install dependencies ──────────────────────────────────
pip install -r requirements.txt

# ── Step 4: Configure environment variables ───────────────────────
cp .env.example .env
# Open .env in your editor and fill in real values (see section 2)

# ── Step 5: Create MySQL database ─────────────────────────────────
mysql -u root -p
# Inside MySQL shell:
#   CREATE DATABASE wildshield_karnataka CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#   exit;

# ── Step 6: Create tables ──────────────────────────────────────────
python3 database/models.py

# ── Step 7: Seed synthetic demo data ─────────────────────────────
python3 database/seed_data.py

# ── Step 8: Run the application ───────────────────────────────────
streamlit run app.py
# Opens at: http://localhost:8501
```

---

## 2. Environment Variables Reference

### Local `.env` file

```dotenv
# ──────────────────────────────────────────────────
#  AGENT 1 — IBM Watsonx.ai (Risk Assessment)
# ──────────────────────────────────────────────────
WATSONX_API_KEY_1=your_ibm_watsonx_api_key_here
WATSONX_PROJECT_ID_1=your_watsonx_project_id_here
WATSONX_MODEL_ID_1=ibm/granite-13b-instruct-v2
WATSONX_URL_1=https://us-south.ml.cloud.ibm.com

# ──────────────────────────────────────────────────
#  AGENT 2 — Replicate API (Safety Advisor)
#  IBM Granite 4.2-8B via Replicate
# ──────────────────────────────────────────────────
REPLICATE_API_KEY=your_replicate_api_token_here
REPLICATE_MODEL_ID=ibm-granite/granite-4.2-8b

# ──────────────────────────────────────────────────
#  DATABASE — MySQL
# ──────────────────────────────────────────────────
DB_HOST=localhost
DB_PORT=3306
DB_NAME=wildshield_karnataka
DB_USER=root
DB_PASSWORD=your_mysql_password_here

# ──────────────────────────────────────────────────
#  APPLICATION
# ──────────────────────────────────────────────────
APP_ENV=development
APP_DEBUG=false
LOG_LEVEL=INFO
```

### Where to get API keys

| Key | Source |
|---|---|
| `WATSONX_API_KEY_1` | IBM Cloud → IAM → API Keys → Create |
| `WATSONX_PROJECT_ID_1` | IBM Watsonx.ai → Projects → Your Project → Manage → Details |
| `WATSONX_URL_1` | Based on region: `us-south.ml.cloud.ibm.com` (US), `eu-de.ml.cloud.ibm.com` (EU) |
| `REPLICATE_API_KEY` | [replicate.com/account/api-tokens](https://replicate.com/account/api-tokens) |

---

## 3. Streamlit Cloud Deployment

### Step 1 — Prepare your GitHub repository

```bash
# Make sure .env is NOT committed (it's in .gitignore already)
git add .
git commit -m "feat: Wild Shield Karnataka — hackathon submission"
git push origin main
```

### Step 2 — Connect to Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **New app**
4. Select your repository and branch (`main`)
5. Set **Main file path** to `app.py`
6. Click **Deploy**

### Step 3 — Add Secrets

In Streamlit Cloud: **App settings → Secrets** — paste the following:

```toml
# Streamlit Cloud Secrets (TOML format)
# ─────────────────────────────────────
# Agent 1 — IBM Watsonx.ai
WATSONX_API_KEY_1    = "your_watsonx_api_key"
WATSONX_PROJECT_ID_1 = "your_watsonx_project_id"
WATSONX_MODEL_ID_1   = "ibm/granite-13b-instruct-v2"
WATSONX_URL_1        = "https://us-south.ml.cloud.ibm.com"

# Agent 2 — Replicate
REPLICATE_API_KEY    = "your_replicate_api_token"
REPLICATE_MODEL_ID   = "ibm-granite/granite-4.2-8b"

# MySQL (use a cloud-hosted DB for Streamlit Cloud)
DB_HOST     = "your-cloud-mysql-host.example.com"
DB_PORT     = "3306"
DB_NAME     = "wildshield_karnataka"
DB_USER     = "wildshield_user"
DB_PASSWORD = "your_secure_db_password"
```

### Step 4 — Cloud MySQL Options (Free Tier)

| Provider | Free Tier | Setup |
|---|---|---|
| **PlanetScale** | 5GB storage | [planetscale.com](https://planetscale.com) |
| **Aiven** | 1 node, 1GB | [aiven.io](https://aiven.io) |
| **Railway** | $5 credit/mo | [railway.app](https://railway.app) |
| **TiDB Cloud** | 5GB serverless | [tidbcloud.com](https://tidbcloud.com) |

After creating a cloud MySQL database:
```bash
# Apply schema to cloud DB
DB_HOST=your-cloud-host DB_USER=your-user DB_PASSWORD=your-pass \
  python3 database/models.py

# Seed synthetic data
DB_HOST=your-cloud-host DB_USER=your-user DB_PASSWORD=your-pass \
  python3 database/seed_data.py
```

---

## 4. Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all 143 tests
python3 tests/run_all_tests.py

# Run specific test suites
python3 -m pytest tests/test_agent1.py -v         # Agent 1: 41 tests
python3 -m pytest tests/test_agent2.py -v         # Agent 2: 36 tests
python3 -m pytest tests/test_orchestrator.py -v   # Orchestrator: 29 tests
python3 -m pytest tests/test_utils.py -v          # Utilities: 37 tests

# Test live API connections (needs real keys in .env)
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

## 5. Fallback Mode (No API Keys)

The application works without API keys using rule-based fallback:

- **Agent 1 fallback:** Pure rule-based risk scoring from incident frequency, recency, species, and proximity — no LLM call.
- **Agent 2 fallback:** Pre-written template advisories selected by risk level — no LLM call.
- **DB fallback:** If MySQL is unavailable, reads from `data/synthetic/sample_incidents.csv` directly.

This allows a **complete demo without any cloud credentials** — all 5 dashboard pages remain functional.

---

## 6. Troubleshooting

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` inside `venv` |
| MySQL connection refused | Ensure MySQL service is running: `sudo systemctl start mysql` |
| `Access denied for user 'root'@'localhost'` | Check `DB_PASSWORD` in `.env` |
| `WATSONX_API_KEY_1 is not configured` | Add key to `.env`; app still works in fallback mode |
| Streamlit Cloud: `Secrets not found` | Paste secrets in App Settings → Secrets (TOML format) |
| Folium map not rendering | Ensure `streamlit-folium` is in requirements.txt |
| Kannada text garbled | Ensure browser charset is UTF-8 (default in all modern browsers) |

---

## 7. Security Checklist

- [ ] `.env` is in `.gitignore` — never committed to GitHub
- [ ] API keys are only in `.env` (local) or Streamlit Secrets (production)
- [ ] No API keys in any Python source file
- [ ] No API keys in any log output
- [ ] `is_synthetic = TRUE` on all demonstration data
- [ ] Advisory validation rejects real-time animal location claims
- [ ] No real village GPS coordinates or forest patrol routes exposed
