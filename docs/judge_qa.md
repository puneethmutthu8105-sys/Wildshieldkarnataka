# Wild Shield Karnataka — Judge Q&A Preparation Guide

> 20 questions judges commonly ask at IBM hackathons — with model answers for your team.
> Read these aloud before the presentation. Know the answers without reading.

---

## SECTION A — Project Understanding

### Q1. What problem does Wild Shield Karnataka solve?

**Answer:**
Villages near Karnataka's forests face human–wildlife conflicts involving elephants, leopards, wild boars, and other species. Delayed warnings and scattered incident reports increase risk to residents, farmers, livestock, and wildlife. Wild Shield Karnataka analyses historical wildlife incident data to identify potential conflict hotspots, assess risk levels, and generate localized safety advisories in both Kannada and English — helping communities and forest officials take preventive action.

---

### Q2. Why is this problem important and relevant to Karnataka?

**Answer:**
Karnataka has over 5,000 km² of protected forests and national parks including Nagarhole, Bandipur, Dandeli, and BRT Wildlife Sanctuary. Thousands of villages lie on the forest fringe. Human–wildlife conflict has been a persistent issue — elephant crop raids, leopard attacks near villages, and accidental encounters with wild boars are frequently reported. A data-driven, AI-powered early warning and advisory system directly addresses a real, documented need in this region.

---

### Q3. What is the core innovation of your project?

**Answer:**
Three innovations:
1. **Two-agent AI pipeline** — Agent 1 handles analytical risk intelligence; Agent 2 handles safety communication. Their responsibilities are clearly separated.
2. **Bilingual safety advisories** — Kannada output makes the system directly usable by rural Karnataka communities who may not read English.
3. **Explainable risk scoring** — every risk score shows the factors that contributed to it, so forest officials can trust and verify the output rather than treating it as a black box.

---

## SECTION B — Technical Architecture

### Q4. Why did you use two separate AI agents instead of one?

**Answer:**
The two agents have fundamentally different responsibilities:
- Agent 1 performs analytical reasoning — it needs consistency and factual output, so we configured it with low temperature (0.2).
- Agent 2 generates natural language communication — advisory messages need to be warm, understandable, and community-friendly, so it uses higher temperature (0.7).

Separating them also makes the system easier to debug, test independently, and swap components (e.g., replace Agent 2's LLM without touching Agent 1). It also accurately reflects a real multi-agent AI design pattern.

---

### Q5. How do the two agents communicate?

**Answer:**
Through a structured Python data class called `RiskAssessmentResult`. After Agent 1 completes its analysis, it returns a typed object containing: risk score, risk classification, identified hotspots, species summary, and a narrative explanation. The Orchestrator passes this directly to Agent 2's `generate_advisory()` method. Agent 2 never touches the raw incident data — it only sees the structured assessment. This is a clean producer–consumer pattern.

---

### Q6. What is the Orchestrator and why is it needed?

**Answer:**
The Orchestrator (`orchestrator.py`) is the coordination layer between the two agents and the dashboard. It:
- Fetches the right incident data from the database for a given village
- Calls Agent 1 and waits for its result
- Passes that result to Agent 2
- Saves both outputs to MySQL
- Reports progress back to the Streamlit dashboard via callback functions

Without the Orchestrator, each dashboard page would need to know how to coordinate the agents directly. The Orchestrator keeps that logic in one place, making the system easier to maintain.

---

### Q7. How is IBM Granite used in this project?

**Answer:**
IBM Granite is used for both agents:
- **Agent 1** uses IBM Granite 13B Instruct via IBM Watsonx.ai. It receives a structured prompt containing incident statistics and returns a natural language risk explanation.
- **Agent 2** uses IBM Granite 4.2-8B via the Replicate API. It receives the risk assessment and generates Kannada and English safety advisories.

IBM Granite was chosen because it is IBM's enterprise-grade LLM optimized for factual, instruction-following tasks — exactly what an advisory system requires.

---

### Q8. Why are there two different API keys and two LLM configurations?

**Answer:**
The problem statement requires two independent AI agents with two independent API keys and two LLM configurations. This is intentional architectural design:
- Different API keys mean the agents can be billed, rate-limited, and monitored independently.
- Different LLM configurations (temperature, max_tokens) reflect the different output styles each agent needs.
- In a production system, this separation also improves fault isolation — if one API key is exhausted or the service is down, it doesn't affect the other agent.

---

### Q9. How does the risk scoring work?

**Answer:**
The risk score is calculated from four weighted factors:
1. **Incident frequency** — number of incidents in the past 90 days (normalized to 0–40 points)
2. **Species severity weight** — Elephants and Tigers score 10/10; Leopards 9/10; Wild Boars 6/10 (adds 0–25 points)
3. **Recency multiplier** — incidents in the last 30 days get 1.5× weight; last 90 days get 1.2× (adds 0–20 points)
4. **Injury/fatality penalty** — +15 points for any incident involving injury or death (adds 0–15 points)

The total score (0–100) maps to: LOW (<35), MEDIUM (35–64), HIGH (≥65).
Every score includes a human-readable explanation of which factors contributed — it's fully explainable.

---

### Q10. How does the system identify conflict hotspots?

**Answer:**
The system identifies hotspots by clustering incident locations geographically. Villages with more than 3 incidents within a 5 km radius in the past 90 days are flagged as potential hotspots. These are highlighted on the Folium interactive map with color-coded markers — red for HIGH risk, orange for MEDIUM, green for LOW. The map also shows approximate incident clusters so forest officials can visually see which areas need attention.

---

## SECTION C — Data & Safety

### Q11. What data does the system use? Is it real data?

**Answer:**
For this hackathon demonstration, we use synthetic data — 45 carefully crafted incident records across 11 Karnataka villages. All synthetic records are explicitly labeled `is_synthetic = TRUE` in the database. We never present this as real verified data.

The system is designed to work with real historical wildlife incident data from Karnataka Forest Department records, the Wildlife Institute of India, or community reporting systems. The database schema and agent inputs are structured to accept real data without code changes.

---

### Q12. Why doesn't the system claim real-time wildlife tracking?

**Answer:**
Claiming real-time wildlife location would be both technically dishonest (we don't have GPS collar data or live sensor feeds) and potentially dangerous — if people believe an animal is in a specific location based on stale data, they might walk into a conflict zone.

Our system is explicit: all risk assessments are based on **historical patterns**, not confirmed current animal positions. Every advisory includes a disclaimer clarifying this. This is the responsible and truthful way to build a wildlife safety system.

---

### Q13. How does the system protect sensitive wildlife information?

**Answer:**
Three measures:
1. No specific animal GPS coordinates or wildlife patrol routes are stored or displayed.
2. Only approximate incident cluster locations are shown on maps — not pin-point animal positions.
3. Agent 2's advisory validation explicitly rejects any generated text that claims to know the current location of a specific animal — such output is replaced with the template advisory before display.

---

## SECTION D — IBM Cloud & IBM Bob

### Q14. How is IBM Cloud used in this project?

**Answer:**
IBM Cloud provides the IBM Watsonx.ai service that powers Agent 1. We use the `ibm-watsonx-ai` Python SDK to call the IBM Granite LLM via the Watsonx.ai inference endpoint. For production deployment, IBM Cloud also provides the infrastructure for hosting, storage, and service management. IBM Cloud's IAM (Identity and Access Management) manages our API keys securely.

---

### Q15. How did IBM Bob help in building this project?

**Answer:**
IBM Bob was our AI development assistant throughout all five steps:
- **Step 1:** Bob helped design the system architecture, compare three technical approaches, and plan the database schema and dashboard layout.
- **Step 2:** Bob guided agent implementation, LLM integration, and orchestrator design.
- **Step 3:** Bob assisted with Streamlit dashboard construction, map integration, and bilingual advisory display.
- **Step 4:** Bob helped design 143 test cases covering all agents, the orchestrator, and utilities.
- **Step 5:** Bob helped finalize deployment, documentation, and this presentation.

Bob was used exactly as intended — as an AI-assisted software engineering tool that accelerated development while keeping the team in full control of technical decisions.

---

## SECTION E — Implementation & Quality

### Q16. How did you test the system?

**Answer:**
We built 143 unit and integration tests covering:
- Agent 1: 41 tests (risk scoring, hotspot identification, LLM fallback, edge cases)
- Agent 2: 36 tests (advisory generation, Kannada output, validation, fallback mode)
- Orchestrator: 29 tests (pipeline coordination, error handling, DB persistence)
- Utilities: 37 tests (scoring math, text formatting, validation rules)

All 143/143 tests pass. The test suite runs without real API keys — agents use deterministic fallback logic when LLMs are unavailable, so tests are reproducible and CI-friendly.

---

### Q17. What happens if an API key is missing or the LLM API is down?

**Answer:**
Both agents have graceful fallback mechanisms:
- If Agent 1's LLM call fails, it uses pure rule-based risk scoring (still explainable and accurate).
- If Agent 2's LLM call fails, it selects a pre-written template advisory matching the risk level.
- If MySQL is unavailable, the app reads from the CSV file directly.

The app never crashes. All 5 dashboard pages remain functional even with zero API keys configured.

---

### Q18. How does the Kannada language generation work?

**Answer:**
Agent 2 receives the English risk assessment and uses a dedicated Kannada prompt to generate the advisory. The IBM Granite 4.2-8B model on Replicate has multilingual capability. We explicitly prompt it with: "Generate this safety advisory in Kannada language (ಕನ್ನಡ). Use simple language that rural communities can understand." The output is validated and displayed using UTF-8 encoding with appropriate font handling in Streamlit. If the LLM output fails Kannada detection, the fallback provides a pre-written template advisory in Kannada.

---

### Q19. Can this system scale to other states or wildlife zones?

**Answer:**
Yes. The system is designed to be location-agnostic:
- The database schema supports any villages table with lat/lon coordinates.
- The risk scoring engine uses configurable species weights — adding a new species requires one line of configuration.
- The advisory prompts reference the village name and species dynamically — no hardcoded Karnataka-specific logic.
- Scaling to Goa, Kerala, or Maharashtra would require uploading the relevant incident data and village records. No code changes needed.

---

### Q20. What would you build next if you had more time?

**Answer:**
Three high-value next features:
1. **Community reporting module** — a simple mobile-friendly form where villagers can report new sightings directly into the system, keeping the data fresh.
2. **SMS/WhatsApp alert integration** — connect Agent 2's advisories to Twilio or WhatsApp Business API so advisories are pushed to village heads automatically when risk crosses HIGH threshold.
3. **Historical trend analysis** — a time-series model (LSTM or Prophet) to predict seasonal risk spikes based on 3–5 years of historical data, giving forest departments advance warning before peak conflict months.

These extensions would transform Wild Shield Karnataka from a demonstration system into a production-ready forest management tool.

---

## Presentation Tips

- **Demo order:** Main Dashboard → Risk Map → Run Agent Pipeline → Advisory Page → Agent Console
- **Highest-risk village for demo:** Nagapura (score 68 — HIGH risk) — most dramatic result
- **If asked "is this real data?"** — answer immediately and confidently: "All demo data is synthetic and clearly labeled `is_synthetic = TRUE`. The system is built to accept real Karnataka Forest Department data without code changes."
- **If a live API call fails during demo:** explain fallback mode — "The app continues to function with rule-based scoring and template advisories even without API connectivity."
- **Time target:** Keep live demo under 5 minutes. Use `docs/demo_script.md` as your guide.
