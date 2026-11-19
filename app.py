# ============================================================
# app.py
# Wild Shield Karnataka — Streamlit Application Entry Point
#
# Run with:   streamlit run app.py
# ============================================================

import os
import sys
import logging

import streamlit as st

# ---- Page configuration (MUST be the very first Streamlit call) ----
st.set_page_config(
    page_title="Wild Shield Karnataka",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": (
            "**Wild Shield Karnataka** — Human–Wildlife Conflict Prevention System\n\n"
            "AI-powered multi-agent platform using IBM Granite + IBM Cloud.\n\n"
            "⚠️ Uses synthetic demonstration data only.\n"
            "Does NOT track real-time wildlife locations."
        )
    },
)

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---- Custom CSS ----
def _load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path, encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

_load_css()


# ---- Imports ----
from dashboard.main_page       import render_main_dashboard
from dashboard.risk_page       import render_risk_dashboard
from dashboard.advisory_page   import render_advisory_dashboard
from dashboard.incident_page   import render_incident_history
from dashboard.agent_console_page import render_agent_console
from orchestrator.orchestrator import WildShieldOrchestrator
from config.settings           import validate_config
from database.connection       import test_connection


# ============================================================
# Session State Initialization
# ============================================================
if "orchestrator" not in st.session_state:
    with st.spinner("Initializing Wild Shield Karnataka..."):
        st.session_state["orchestrator"] = WildShieldOrchestrator()

if "last_risk_result" not in st.session_state:
    st.session_state["last_risk_result"] = None


# ============================================================
# Sidebar Navigation
# ============================================================
with st.sidebar:
    # Logo / title
    st.markdown(
        """
        <div style="padding:0.5rem 0 1rem 0">
            <div style="font-size:1.5rem;font-weight:800;color:#1a4731">
                🐘 Wild Shield
            </div>
            <div style="font-size:0.8rem;color:#57606a;margin-top:2px">
                Karnataka · Human–Wildlife Conflict
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation",
        options=[
            "📊 Main Dashboard",
            "🗺️ Risk Assessment",
            "🤖 AI Agent Console",
            "📢 Safety Advisories",
            "📋 Incident History",
            "ℹ️ About",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # ── DB status ─────────────────────────────────────────────────
    db_status = test_connection()
    if db_status["connected"]:
        st.success(f"🗄️ DB: Connected\n`{db_status['database']}`")
    else:
        st.info("🗄️ Demo Mode\n*(CSV data · no DB needed)*")

    # ── LLM status (live inference check, cached per session) ─────
    cfg_ok = validate_config()["valid"]
    if not cfg_ok:
        st.warning("🤖 LLMs: Not configured\n*(Template fallback active)*")
    else:
        # Cache the live inference check so it only runs once per session
        if "llm_inference_ok" not in st.session_state:
            st.session_state["llm_inference_ok"] = None  # None = not checked yet
        
        if st.session_state["llm_inference_ok"] is None:
            # First page load — test live inference quietly
            try:
                orchestrator_ref = st.session_state.get("orchestrator")
                if orchestrator_ref:
                    r1 = orchestrator_ref.agent1.test_llm_connection()
                    st.session_state["llm_inference_ok"] = r1["connected"]
                    st.session_state["llm_error"] = r1.get("error", "")
                else:
                    st.session_state["llm_inference_ok"] = False
                    st.session_state["llm_error"] = "Orchestrator not ready"
            except Exception as e:
                st.session_state["llm_inference_ok"] = False
                st.session_state["llm_error"] = str(e)

        if st.session_state["llm_inference_ok"]:
            st.success("🤖 LLMs: Connected ✅\n*(IBM Granite — Live)*")
        else:
            err = st.session_state.get("llm_error", "")
            if "no_associated_service_instance" in err:
                st.error("🤖 LLMs: Project not linked to WML\n*(Template fallback active)*")
            elif "invalid_instance_status" in err:
                st.error("🤖 LLMs: WML instance inactive\n*(Template fallback active)*")
            elif "403" in err or "401" in err:
                st.error("🤖 LLMs: Auth failed\n*(Template fallback active)*")
            else:
                st.warning("🤖 LLMs: Configured — inference pending\n*(Click Run to test)*")

    st.divider()

    # ── Last analysis summary ─────────────────────────────────────
    if st.session_state.get("last_risk_result"):
        result = st.session_state["last_risk_result"]
        if result.success:
            ra = result.risk_assessment
            risk_color = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}.get(
                ra.risk_level, "#6b7280"
            )
            st.markdown("**Last Analysis:**")
            st.markdown(
                f'<div style="font-size:0.82rem">'
                f'📍 {ra.village_name}<br>'
                f'Score: <strong style="color:{risk_color}">{ra.risk_score}/100</strong><br>'
                f'<span class="badge badge-{ra.risk_level}" '
                f'style="font-size:0.7rem">{ra.risk_level}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.divider()

    # ── Disclaimer ────────────────────────────────────────────────
    st.caption(
        "⚠️ Synthetic demo data only.\n"
        "No real animal locations.\n"
        "Not real-time tracking."
    )


# ============================================================
# Configuration Warning Banner
# ============================================================
cfg = validate_config()
if not cfg["valid"]:
    with st.expander("⚙️ LLM Configuration Required (click to expand)", expanded=False):
        st.warning(
            "IBM Granite API keys are not configured. "
            "The app runs with template-based advisories.\n\n"
            "Add your credentials to `.env` to enable live LLM features:"
        )
        for err in cfg["errors"]:
            st.markdown(f"- {err}")
        st.code(
            "# Edit .env file:\n"
            "WATSONX_API_KEY_1=your_ibm_watsonx_api_key\n"
            "WATSONX_PROJECT_ID_1=your_watsonx_project_id\n"
            "REPLICATE_API_KEY=your_replicate_token",
            language="bash",
        )


# ============================================================
# Page Routing
# ============================================================
orchestrator = st.session_state["orchestrator"]

if page == "📊 Main Dashboard":
    render_main_dashboard(orchestrator)

elif page == "🗺️ Risk Assessment":
    render_risk_dashboard(orchestrator)

elif page == "🤖 AI Agent Console":
    render_agent_console(orchestrator)

elif page == "📢 Safety Advisories":
    render_advisory_dashboard(orchestrator)

elif page == "📋 Incident History":
    render_incident_history(orchestrator)

elif page == "ℹ️ About":
    st.title("ℹ️ About Wild Shield Karnataka")

    st.markdown(
        """
        <div class="wsk-header">
            <h1>🐘 Wild Shield Karnataka</h1>
            <p>Human–Wildlife Conflict Prevention System</p>
            <p class="tagline">IBM Granite · IBM Cloud · Two-Agent Architecture · Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
            ## 🎯 Project Overview
            **Wild Shield Karnataka** is an AI-powered human–wildlife conflict prevention
            platform built for the **Inter-Institute IBM Bob Hackathon with IBM SkillsBuild**.

            Villages near Karnataka's forests face recurring encounters with elephants,
            leopards, wild boars, and other wildlife. This system analyses historical
            incident data to identify risk hotspots and generate safety advisories for
            communities and forest officials.

            ---

            ## 🤖 Two-Agent Architecture

            | Agent | Role | LLM |
            |---|---|---|
            | **Agent 1 — Risk Assessment** | Analyses historical incidents, scores risk 0-100, identifies hotspots | IBM Granite LLM 1 (API Key 1, temp=0.2) |
            | **Agent 2 — Safety Advisor** | Generates Kannada + English safety advisories | IBM Granite LLM 2 (API Key 2, temp=0.7) |

            **Why two agents?**
            - **Separation of concerns**: Agent 1 is analytical intelligence.
              Agent 2 is communication intelligence.
            - **Independent testing**: Each agent can be tested and debugged independently.
            - **Transparent handoff**: The structured `RiskAssessmentResult` JSON
              contract makes the communication between agents auditable.
            - **Independent LLMs**: Different temperature settings for different tasks.

            ---

            ## 🔑 Scoring System (Agent 1)

            Agent 1 uses a transparent, explainable 0-100 scoring system:

            | Component | Max Points | Description |
            |---|---|---|
            | Incident Frequency | 55 | Based on total historical incident count |
            | Recent Activity Bonus | 15 | If incidents occurred in last 30 days of data |
            | Species Danger | 25 | Based on species type (Tiger=25, Leopard=20...) |
            | Forest Proximity | 15 | Distance of village from forest boundary |

            **Score → Risk Level:**
            - 0-30: 🟢 LOW RISK
            - 31-65: 🟡 MEDIUM RISK
            - 66-100: 🔴 HIGH RISK

            ---

            ## 🛡️ Safety Guardrails (Agent 2)

            Agent 2 enforces strict safety rules:
            - Pre-approved safety templates used as foundation
            - Forbidden phrases list blocks harmful content
            - Advisories NEVER claim real-time animal locations
            - Karnataka Forest Department helpline included for HIGH risk
            - Kannada language detection validates translation quality
            """
        )

    with col2:
        st.markdown("## 🛠️ Tech Stack")
        tech_stack = [
            ("IBM Bob", "AI-assisted development"),
            ("IBM Granite", "LLM backbone (2 configs)"),
            ("IBM Cloud", "Cloud infrastructure"),
            ("Python 3.11+", "Backend + agent logic"),
            ("Streamlit", "Frontend dashboard"),
            ("MySQL", "Database (5 tables)"),
            ("Folium", "Interactive maps"),
            ("Plotly", "Charts & visualizations"),
            ("Pandas", "Data processing"),
        ]
        for tech, desc in tech_stack:
            st.markdown(
                f'<div style="padding:0.4rem 0;border-bottom:1px solid #f3f4f6">'
                f'<strong style="font-size:0.85rem">{tech}</strong>'
                f'<div style="font-size:0.78rem;color:#57606a">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("## ⚠️ Disclaimers")
        st.warning(
            "This system does **NOT** track real-time wildlife locations.\n\n"
            "All data is synthetic demonstration data "
            "(`is_synthetic = TRUE`).\n\n"
            "Risk assessments are based on **historical patterns** only."
        )

        st.markdown("## 📞 Emergency Contact")
        st.info(
            "**Karnataka Forest Department**\n\n"
            "Helpline: **1800-425-7979** (Toll-free)"
        )

    st.markdown(
        '<div class="wsk-footer">Wild Shield Karnataka · IBM Granite + IBM Cloud · '
        'Inter-Institute IBM Bob Hackathon with IBM SkillsBuild · Problem Statement #28</div>',
        unsafe_allow_html=True,
    )
