# Wild Shield Karnataka — Live Demo Script
## 5-Minute Structured Walkthrough for Hackathon Judges

---

> **Before you start:**
> - App is running at `http://localhost:8501` (or your Streamlit Cloud URL)
> - Database is seeded with 45 synthetic incidents
> - Synthetic data disclaimer is visible on the main dashboard
> - Timer: aim for exactly 5 minutes

---

## ⏱️ MINUTE 0:00 — OPENING (30 seconds)

**Say:**
> "Wild Shield Karnataka is an AI-powered human–wildlife conflict prevention system for villages near Karnataka's forests. It uses two independent AI agents — both powered by IBM Granite — to analyse historical wildlife incidents and generate localized safety advisories in both Kannada and English. Let me walk you through it."

**Action:** App should be open on the **Main Dashboard** already.

---

## ⏱️ MINUTE 0:30 — MAIN DASHBOARD (60 seconds)

**Say:**
> "This is our main dashboard. You can see at the top — 45 reported incidents, 11 affected villages, and a breakdown of risk levels. Notice the data disclaimer — all demo data is synthetic and clearly labeled. We do not use real wildlife locations."

**Point to / click:**
- 🔢 KPI cards (incident count, village count, HIGH/MEDIUM/LOW risk counts)
- 📈 Historical trend chart — "Incidents are higher in certain months — this correlates with crop harvest season when elephants typically venture closer to settlements."
- 🍩 Species distribution donut — "Elephants account for the majority of reported incidents in our synthetic dataset."

**Say:**
> "Every number here is driven by real database queries from MySQL — not hardcoded."

---

## ⏱️ MINUTE 1:30 — RISK ASSESSMENT MAP (90 seconds)

**Action:** Click **"🗺️ Risk Assessment"** in the sidebar.

**Say:**
> "This is the risk assessment page. The interactive map shows our 11 villages color-coded by risk level — red for HIGH, orange for MEDIUM, green for LOW."

**Action:** Point to the map. Click on a **red marker** (Nagapura).

**Say:**
> "Nagapura is our highest-risk village with a score of 68 out of 100. Let me show you how Agent 1 calculates this."

**Action:** In the village selector dropdown, choose **Nagapura**. Click **"Run Agent 1 — Risk Assessment"**.

**While it runs:**
> "Agent 1 is now querying the database for historical incidents in Nagapura, applying our weighted risk scoring model — which accounts for incident frequency, species severity, recency, and injury data — and then calling IBM Granite via Watsonx.ai to generate a narrative explanation."

**When result appears:**
> "Score: 68, classification: HIGH RISK. The explanation shows exactly which factors contributed — high elephant incident frequency, two injury incidents in the last 30 days, and forest proximity under 2 km. This is fully explainable AI — not a black box."

---

## ⏱️ MINUTE 3:00 — SAFETY ADVISORIES (60 seconds)

**Action:** Click **"📢 Safety Advisories"** in the sidebar.

**Say:**
> "Agent 2 — our Safety Advisor — has taken Agent 1's risk assessment and generated localized advisories."

**Point to the Kannada advisory card:**
> "This is the Kannada language advisory — simple, direct language that rural Karnataka communities can understand without technical terminology."

**Point to the English advisory card:**
> "And here is the equivalent English advisory. Notice the disclaimer at the bottom — it explicitly states this is based on historical patterns, not confirmed current animal movements."

**Point to precautions list:**
> "The precautionary actions are specific to both the risk level and the species involved. HIGH RISK advisories recommend contacting the forest department. LOW RISK advisories focus on general awareness."

---

## ⏱️ MINUTE 4:00 — AGENT CONSOLE (45 seconds)

**Action:** Click **"⚙️ Agent Console"** in the sidebar.

**Say:**
> "The Agent Console is for forest officials and technical reviewers. It shows the complete pipeline in real time."

**Point to the architecture section:**
> "Here you can see exactly how the two agents communicate — Agent 1 produces a structured RiskAssessmentResult JSON object, and Agent 2 receives it as input. The agents have clean, separated responsibilities."

**Point to the JSON viewer:**
> "This is the raw structured output from Agent 1 — the exact JSON payload passed to Agent 2. Full transparency into what the AI is doing."

---

## ⏱️ MINUTE 4:45 — CLOSING (15 seconds)

**Say:**
> "Wild Shield Karnataka demonstrates how two independent IBM Granite-powered AI agents can work together to support wildlife conservation and rural safety in Karnataka. Historical risk analysis plus localized bilingual advisories — built with IBM Bob, IBM Cloud, Python, and Streamlit. Thank you."

---

## 📋 Fallback Plan

**If the LLM API fails during demo:**
> "You'll notice the app continues to work — Agent 1 uses rule-based risk scoring and Agent 2 uses pre-written template advisories. This is intentional — the system is designed to be resilient and always usable, even without API connectivity."

**If a judge asks about real data:**
> "All data in this demo is synthetic and clearly labeled `is_synthetic = TRUE`. The system is architected to accept real Karnataka Forest Department incident data without any code changes."

**If Streamlit is slow to load:**
> "While it loads, let me explain the two-agent architecture..." (use the architecture section of this script)

---

## ✅ Pre-Demo Checklist

- [ ] App is running (`streamlit run app.py`)
- [ ] Database is seeded (`python3 database/seed_data.py`)
- [ ] Browser is on Main Dashboard page
- [ ] Sidebar is visible
- [ ] Folium map loads correctly (test before presentation)
- [ ] API keys are configured (or confirm fallback mode works)
- [ ] Screen resolution is readable from a distance (zoom browser to 125%)
- [ ] Team member roles assigned: 1 presenter, 1 driving the mouse
- [ ] Timer visible (phone or watch)
- [ ] README.md open in another tab for reference

---

## 🗣️ Key Phrases to Use

| When | Say |
|---|---|
| Opening | "Two independent AI agents powered by IBM Granite" |
| Risk map | "Color-coded by risk level — this is not hardcoded, it's computed from historical data" |
| Risk score | "Fully explainable AI — every factor is visible" |
| Kannada advisory | "Simple language for rural communities" |
| Data disclaimer | "Synthetic demonstration data — clearly labeled throughout" |
| Closing | "Built with IBM Bob, IBM Cloud, Python, and Streamlit" |

---

## ⏱️ Time Budget

| Section | Time |
|---|---|
| Opening | 0:30 |
| Main Dashboard | 1:00 |
| Risk Assessment Map + Agent 1 | 1:30 |
| Safety Advisories | 1:00 |
| Agent Console | 0:45 |
| Closing | 0:15 |
| **Total** | **5:00** |
