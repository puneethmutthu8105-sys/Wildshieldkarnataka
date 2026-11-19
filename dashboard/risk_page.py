# ============================================================
# dashboard/risk_page.py
# Wild Shield Karnataka — Risk Assessment Dashboard (Full Implementation)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from utils.helpers import (
    get_risk_color,
    prepare_map_data,
    calculate_village_risk_summary,
    get_species_emoji,
)


RISK_COLORS = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a", "UNKNOWN": "#6b7280"}
MARKER_COLORS = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green", "UNKNOWN": "gray"}


def _get_risk_badge_html(risk_level: str) -> str:
    return f'<span class="badge badge-{risk_level}">{risk_level}</span>'


def render_risk_dashboard(orchestrator):
    """
    Render the Risk Assessment dashboard.
    Includes interactive Folium map, village selector, and live Agent 1 execution.
    """
    st.title("🗺️ Risk Assessment Dashboard")
    st.markdown(
        "Identify potential human–wildlife conflict hotspots using historical data. "
        "Run Agent 1 on any village to get a full risk assessment."
    )
    st.markdown(
        '<div class="synthetic-banner">'
        '⚠️ <strong>Demo Mode:</strong> All incidents are synthetic demonstration data. '
        'Risk assessments are based on these synthetic records only.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Load data ────────────────────────────────────────────────
    with st.spinner("Loading incident data..."):
        df = orchestrator.get_all_incidents()

    if df.empty:
        st.warning("No incident data found. Please check your data source.")
        return

    # ── Layout: map on left, controls on right ────────────────────
    col_map, col_control = st.columns([3, 2])

    with col_map:
        st.subheader("🗺️ Incident Map")
        _render_incident_map(df)

    with col_control:
        _render_risk_runner(orchestrator, df)

    st.divider()

    # ── Village risk scorecard (populated from previous runs) ──────
    _render_village_scorecard(df)

    # ── Species analysis chart ─────────────────────────────────────
    st.divider()
    _render_species_analysis(df)


def _render_incident_map(df: pd.DataFrame):
    """Render an interactive Folium map with incident markers."""
    map_data = prepare_map_data(df)

    # Center map on Karnataka
    karnataka_center = [13.0827, 76.5]
    m = folium.Map(
        location=karnataka_center,
        zoom_start=7,
        tiles="OpenStreetMap",
    )

    # Color by severity
    severity_to_color = {"HIGH": "red", "MEDIUM": "orange", "LOW": "green"}

    for point in map_data:
        try:
            lat = float(point["latitude"])
            lon = float(point["longitude"])
            sev = str(point.get("severity", "MEDIUM")).upper()
            species = str(point.get("species", "Wildlife"))
            village = str(point.get("village_name", "Unknown"))
            inc_date = str(point.get("incident_date", ""))
            color = severity_to_color.get(sev, "gray")
            sev_color = severity_to_color.get(sev, "gray")

            popup_html = (
                f"<div style='font-family:sans-serif;min-width:160px'>"
                f"<b style='font-size:0.85rem'>{get_species_emoji(species)} {species}</b><br>"
                f"<span style='font-size:0.8rem;color:#374151'>{village}</span><br>"
                f"<span style='font-size:0.75rem;color:#57606a'>{inc_date}</span><br>"
                f"<span style='font-size:0.75rem;color:{sev_color}'>"
                f"Severity: {sev}</span>"
                f"</div>"
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.75,
                popup=folium.Popup(popup_html, max_width=220),
                tooltip=f"{species} — {village}",
            ).add_to(m)
        except (TypeError, ValueError):
            continue

    # Legend
    legend_html = """
    <div style='position:fixed;bottom:30px;left:30px;background:white;
         padding:10px 14px;border-radius:8px;border:1px solid #e5e7eb;
         font-size:12px;font-family:sans-serif;z-index:1000;'>
        <b>Incident Severity</b><br>
        <span style='color:red'>●</span> HIGH &nbsp;
        <span style='color:orange'>●</span> MEDIUM &nbsp;
        <span style='color:green'>●</span> LOW
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    st_folium(m, width="100%", height=420, returned_objects=[])


def _render_risk_runner(orchestrator, df: pd.DataFrame):
    """Render the village selector and Agent 1 execution panel."""
    st.subheader("🤖 Run Risk Assessment")

    villages = sorted(df["village_name"].unique().tolist())
    selected_village = st.selectbox(
        "Select village to analyse:",
        villages,
        help="Choose a village — Agent 1 will analyse its historical incident data.",
    )

    # Show quick stats for selected village
    village_df = df[df["village_name"] == selected_village]
    if not village_df.empty:
        st.markdown(
            f'<div style="background:#f7f8fa;border-radius:8px;'
            f'padding:0.6rem 1rem;margin:0.5rem 0;font-size:0.85rem">'
            f'📊 <strong>{len(village_df)} incidents</strong> · '
            f'Species: {", ".join(village_df["species"].unique()[:3])}'
            f'</div>',
            unsafe_allow_html=True,
        )

    run_btn = st.button(
        "🤖 Run Agent 1: Risk Assessment",
        type="primary",
        use_container_width=True,
    )

    if run_btn:
        # Progress display
        progress_messages = []
        status_placeholder = st.empty()
        progress_container = st.container()

        def on_progress(msg: str):
            progress_messages.append(msg)
            with progress_container:
                for m in progress_messages[-5:]:
                    st.caption(f"⚙️ {m}")

        with st.spinner(f"Agent 1 analysing {selected_village}..."):
            result = orchestrator.run_full_analysis(
                selected_village,
                use_db=False,
                on_progress=on_progress,
            )

        status_placeholder.empty()

        if result.success:
            ra = result.risk_assessment
            st.success("✅ Agent 1 analysis complete!")

            # Risk score display
            score_color = get_risk_color(ra.risk_level)
            bar_class = ra.risk_level.lower()

            st.markdown(
                f'<div class="score-display">'
                f'<div class="score-number" style="color:{score_color}">'
                f'{ra.risk_score}'
                f'<span class="score-denom">/100</span>'
                f'</div>'
                f'<div style="margin-top:0.5rem">'
                f'{_get_risk_badge_html(ra.risk_level)}'
                f'</div>'
                f'<div class="score-bar-track" style="margin-top:0.6rem">'
                f'<div class="score-bar-fill {bar_class}" '
                f'style="width:{ra.risk_score}%"></div>'
                f'</div>'
                f'<div class="score-label">Risk Score</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # Score breakdown
            st.markdown("**📊 Score Breakdown:**")
            breakdown = ra.scoring_breakdown
            breakdown_items = {
                "Incident Frequency": breakdown.get("incident_frequency", 0),
                "Recent Activity": breakdown.get("recent_activity_bonus", 0),
                "Species Danger": breakdown.get("species_danger", 0),
                "Forest Proximity": breakdown.get("forest_proximity", 0),
            }
            for label, pts in breakdown_items.items():
                if pts > 0:
                    st.caption(f"• {label}: +{pts:.0f} pts")

            # LLM status
            llm_class = "active" if ra.llm_available else "fallback"
            llm_text = "IBM Granite LLM 1" if ra.llm_available else "Fallback narrative"
            st.markdown(
                f'Analysis by: <span class="llm-pill {llm_class}">{llm_text}</span>',
                unsafe_allow_html=True,
            )

            # Risk factors
            with st.expander("🔍 Risk Factors", expanded=True):
                for factor in ra.risk_factors:
                    st.markdown(f"• {factor}")

            # Analysis summary
            with st.expander("📋 Agent 1 Summary"):
                st.write(ra.analysis_summary)

            # Save result to session state for other pages
            st.session_state["last_risk_result"] = result
            st.info(
                "✅ Advisory generated! Go to **📢 Safety Advisories** to view it."
            )

        else:
            st.error(f"❌ Agent 1 failed: {result.error_message}")


def _render_village_scorecard(df: pd.DataFrame):
    """Render a village-level incident summary table."""
    st.subheader("🏘️ Village Incident Summary")

    summary = calculate_village_risk_summary(df)
    if summary.empty:
        st.info("No village data to display.")
        return

    # Build a richer table
    cols = ["village_name", "district", "incident_count", "top_species"]
    available = [c for c in cols if c in summary.columns]
    display = summary[available].sort_values("incident_count", ascending=False).copy()
    display.columns = [c.replace("_", " ").title() for c in display.columns]

    # Quick bar chart of top villages
    top10 = summary.nlargest(10, "incident_count")
    fig = px.bar(
        top10,
        x="village_name",
        y="incident_count",
        color="incident_count",
        color_continuous_scale=[[0, "#d1fae5"], [0.5, "#d97706"], [1, "#dc2626"]],
        labels={"village_name": "Village", "incident_count": "Incidents"},
    )
    fig.update_layout(
        height=240,
        margin=dict(t=10, b=60, l=0, r=0),
        xaxis=dict(tickangle=-30, gridcolor="#f3f4f6"),
        yaxis=dict(gridcolor="#f3f4f6"),
        coloraxis_showscale=False,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(size=10),
    )
    st.plotly_chart(fig, width="stretch")

    st.dataframe(
        display.reset_index(drop=True),
        width="stretch",
        hide_index=True,
    )


def _render_species_analysis(df: pd.DataFrame):
    """Render species-wise analysis charts."""
    st.subheader("🦌 Species-wise Analysis")

    if "species" not in df.columns:
        return

    col1, col2 = st.columns(2)

    with col1:
        # Incidents by species and incident type
        if "incident_type" in df.columns:
            cross = (
                df.groupby(["species", "incident_type"])
                .size()
                .reset_index(name="count")
            )
            fig = px.bar(
                cross,
                x="species",
                y="count",
                color="incident_type",
                labels={"species": "Species", "count": "Incidents", "incident_type": "Type"},
                barmode="stack",
                color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig.update_layout(
                height=260,
                margin=dict(t=10, b=40, l=0, r=0),
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(size=10),
                xaxis=dict(tickangle=-20),
                legend=dict(font=dict(size=9)),
            )
            st.plotly_chart(fig, width="stretch")
            st.caption("Incidents by species and type")

    with col2:
        # Severity by species
        if "severity" in df.columns:
            sev_cross = (
                df.groupby(["species", "severity"])
                .size()
                .reset_index(name="count")
            )
            sev_colors = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}
            fig2 = px.bar(
                sev_cross,
                x="species",
                y="count",
                color="severity",
                labels={"species": "Species", "count": "Incidents", "severity": "Severity"},
                barmode="group",
                color_discrete_map=sev_colors,
            )
            fig2.update_layout(
                height=260,
                margin=dict(t=10, b=40, l=0, r=0),
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(size=10),
                xaxis=dict(tickangle=-20),
                legend=dict(font=dict(size=9)),
            )
            st.plotly_chart(fig2, width="stretch")
            st.caption("Incident severity by species")
