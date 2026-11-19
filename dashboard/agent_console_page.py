# ============================================================
# dashboard/agent_console_page.py
# Wild Shield Karnataka — AI Agent Console (Full Implementation)
#
# This page shows the live communication between Agent 1 and Agent 2.
# It is the most important page for judge demonstrations —
# it makes the two-agent architecture visible and explainable.
# ============================================================

import json
import streamlit as st
import pandas as pd
import plotly.graph_objects as go


def render_agent_console(orchestrator):
    """
    Render the AI Agent Console page.
    Shows live agent execution, structured JSON handoff, and architecture explanation.
    """
    st.title("🤖 AI Agent Console")
    st.markdown(
        "This console shows how **Agent 1** and **Agent 2** communicate through "
        "the **Wild Shield Karnataka Orchestrator**. "
        "Every step of the two-agent pipeline is visible here."
    )

    # ── Architecture diagram ──────────────────────────────────────
    _render_architecture_diagram()

    st.divider()

    # ── Live execution panel ──────────────────────────────────────
    _render_live_execution(orchestrator)

    st.divider()

    # ── Previous result display ───────────────────────────────────
    if st.session_state.get("last_risk_result"):
        _render_result_detail(st.session_state["last_risk_result"])
    else:
        st.info(
            "No analysis results yet. Use the execution panel above to run an analysis, "
            "or go to **🗺️ Risk Assessment** and run Agent 1 there first."
        )


def _render_architecture_diagram():
    """Render the two-agent workflow as a visual diagram."""
    st.subheader("🏗️ Two-Agent Architecture")

    st.markdown(
        """
        <div style="background:#f7f8fa;border:1px solid #e5e7eb;border-radius:10px;padding:1.2rem 1.5rem;">
        <div class="workflow-step">
            <div class="step-number">1</div>
            <div class="step-content">
                <strong>Historical Incident Data</strong><br>
                Wildlife sighting records loaded from MySQL database (or CSV fallback).
                45 synthetic demo incidents across 11 Karnataka forest-edge villages.
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-number">2</div>
            <div class="step-content">
                <strong>Orchestrator</strong> receives data and passes it to Agent 1.
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-number" style="background:#3b82d4">A1</div>
            <div class="step-content">
                <strong>Agent 1 — Risk Assessment Agent</strong>
                (IBM Granite LLM 1 · API Key 1 · Temperature 0.2)<br>
                Analyses incident frequency, species danger, and forest proximity.
                Calculates a transparent 0-100 risk score with explainable factors.
                Calls IBM Granite to generate a narrative risk summary.
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-number">3</div>
            <div class="step-content">
                <strong>Structured JSON Handoff</strong><br>
                Agent 1 returns a <code>RiskAssessmentResult</code> dataclass —
                a typed, structured JSON object passed to Agent 2.
                This is the contract between the two agents.
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-number" style="background:#7c5cd8">A2</div>
            <div class="step-content">
                <strong>Agent 2 — Safety Advisor Agent</strong>
                (IBM Granite LLM 2 · API Key 2 · Temperature 0.7)<br>
                Reads the risk assessment result. Generates Kannada and English advisories.
                Validates output against safety guardrails before returning.
            </div>
        </div>
        <div class="workflow-step">
            <div class="step-number">4</div>
            <div class="step-content">
                <strong>Orchestrator</strong> saves both outputs to MySQL and returns
                the combined <code>AnalysisResult</code> to the Streamlit dashboard.
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_live_execution(orchestrator):
    """Render the live agent execution panel with real-time progress."""
    st.subheader("▶️ Live Agent Execution")

    df = orchestrator.get_all_incidents()
    if df.empty:
        st.warning("No incident data available.")
        return

    villages = sorted(df["village_name"].unique().tolist())

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        village = st.selectbox(
            "Select village:",
            villages,
            key="console_village_select",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        run_btn = st.button("▶️ Run Pipeline", type="primary", use_container_width=True)

    if run_btn:
        # Collect all progress messages for display
        all_messages: list[str] = []
        agent1_messages: list[str] = []
        agent2_messages: list[str] = []

        log_container = st.container()
        status_text = st.empty()

        def on_progress(msg: str):
            all_messages.append(msg)
            if "[Agent 1]" in msg:
                agent1_messages.append(msg.replace("  [Agent 1] ", ""))
            elif "[Agent 2]" in msg:
                agent2_messages.append(msg.replace("  [Agent 2] ", ""))

            # Determine which agent is active for styling
            is_agent1 = "Agent 1" in msg or "[Agent 1]" in msg
            is_agent2 = "Agent 2" in msg or "[Agent 2]" in msg
            icon = "🔵" if is_agent1 else ("🟣" if is_agent2 else "⚙️")
            status_text.markdown(f"**{icon} {msg}**")

        # Agent 1 status
        st.markdown(
            '<div class="agent-box agent1">'
            '<div class="agent-label a1">AGENT 1 — RISK ASSESSMENT</div>'
            '<span style="font-size:0.85rem;color:#57606a">IBM Granite LLM 1 · Temperature 0.2 (analytical)</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        # Agent 2 status
        st.markdown(
            '<div class="agent-box agent2">'
            '<div class="agent-label a2">AGENT 2 — SAFETY ADVISOR</div>'
            '<span style="font-size:0.85rem;color:#57606a">IBM Granite LLM 2 · Temperature 0.7 (communicative)</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        with st.spinner(f"Running full analysis pipeline for '{village}'..."):
            result = orchestrator.run_full_analysis(
                village, use_db=False, on_progress=on_progress
            )

        status_text.empty()

        if result.success:
            st.success(
                f"✅ Pipeline complete in **{result.total_time_seconds:.2f}s** | "
                f"Risk: **{result.risk_assessment.risk_level}** ({result.risk_assessment.risk_score}/100) | "
                f"Advisory Priority: **{result.safety_advisory.advisory_priority}**"
            )
        else:
            st.error(f"❌ Pipeline failed: {result.error_message}")

        # Show execution log
        with st.expander("📜 Full Execution Log", expanded=False):
            for msg in all_messages:
                icon = "🔵" if "[Agent 1]" in msg else ("🟣" if "[Agent 2]" in msg else "⚙️")
                st.caption(f"{icon} {msg}")

        # Save to session state
        if result.success:
            st.session_state["last_risk_result"] = result


def _render_result_detail(result):
    """Render the detailed output of the last pipeline run."""
    st.subheader("📊 Last Pipeline Results")

    ra = result.risk_assessment
    adv = result.safety_advisory

    # Pipeline timing
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.metric("⏱️ Total Time", f"{result.total_time_seconds:.2f}s")
    with col_t2:
        st.metric("Village", ra.village_name)
    with col_t3:
        st.metric("District", ra.district)

    # Agent 1 and Agent 2 outputs side by side
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<div class="agent-box agent1">'
            '<div class="agent-label a1">AGENT 1 OUTPUT — RiskAssessmentResult</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(f"**Risk Score:** {ra.risk_score}/100")
        st.markdown(
            f'**Risk Level:** <span class="badge badge-{ra.risk_level}">{ra.risk_level}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**Incidents Analysed:** {ra.incident_count}")
        st.markdown(f"**Recent (30d):** {ra.recent_incident_count}")
        st.markdown(f"**Species:** {', '.join(ra.primary_species)}")
        st.markdown(f"**Data Period:** {ra.data_period_start} → {ra.data_period_end}")

        llm_badge = "✅ IBM Granite LLM 1" if ra.llm_available else "⚠️ Fallback narrative"
        st.markdown(f"**LLM Used:** {llm_badge}")

        st.markdown("**Risk Factors:**")
        for f in ra.risk_factors:
            st.caption(f"• {f}")

        st.markdown("**Scoring Breakdown:**")
        breakdown_items = {
            "Frequency": ra.scoring_breakdown.get("incident_frequency", 0),
            "Recent Activity": ra.scoring_breakdown.get("recent_activity_bonus", 0),
            "Species Danger": ra.scoring_breakdown.get("species_danger", 0),
            "Proximity": ra.scoring_breakdown.get("forest_proximity", 0),
        }
        # Mini bar chart
        fig = go.Figure(go.Bar(
            x=list(breakdown_items.values()),
            y=list(breakdown_items.keys()),
            orientation="h",
            marker_color=["#3b82d4", "#7c5cd8", "#dc2626", "#16a34a"],
        ))
        fig.update_layout(
            height=140,
            margin=dict(t=5, b=5, l=0, r=0),
            plot_bgcolor="#ffffff",
            paper_bgcolor="#ffffff",
            font=dict(size=10),
            xaxis=dict(range=[0, 55], gridcolor="#f3f4f6"),
        )
        st.plotly_chart(fig, width="stretch")

        with st.expander("📄 Agent 1 Summary (LLM output)", expanded=False):
            st.write(ra.analysis_summary)

    with col2:
        st.markdown(
            '<div class="agent-box agent2">'
            '<div class="agent-label a2">AGENT 2 OUTPUT — SafetyAdvisoryResult</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'**Priority:** <span class="badge badge-{adv.advisory_priority}">{adv.advisory_priority}</span>',
            unsafe_allow_html=True,
        )
        llm_badge2 = "✅ IBM Granite LLM 2" if adv.llm_available else "⚠️ Template fallback"
        st.markdown(f"**LLM Used:** {llm_badge2}")
        st.markdown(f"**Target:** {', '.join(adv.target_audiences)}")

        st.markdown("**English Advisory (preview):**")
        preview_en = adv.advisory_english[:200] + "..." if len(adv.advisory_english) > 200 else adv.advisory_english
        st.info(preview_en)

        st.markdown("**Kannada Advisory (preview):**")
        preview_kn = adv.advisory_kannada[:180] + "..." if len(adv.advisory_kannada) > 180 else adv.advisory_kannada
        st.info(preview_kn)

    # JSON data contract viewer
    st.divider()
    st.subheader("🔗 Agent 1 → Agent 2 Data Contract (JSON)")
    st.markdown(
        "This is the exact structured JSON that Agent 1 hands to Agent 2. "
        "This typed contract ensures clean, testable communication between agents."
    )

    col_j1, col_j2 = st.columns(2)
    with col_j1:
        with st.expander("📤 Agent 1 Output (RiskAssessmentResult)", expanded=True):
            st.json(ra.to_dict())
    with col_j2:
        with st.expander("📥 Agent 2 Output (SafetyAdvisoryResult)", expanded=True):
            st.json(adv.to_dict())
