# ============================================================
# dashboard/main_page.py
# Wild Shield Karnataka — Main Dashboard (Full Implementation)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.helpers import (
    calculate_incident_trends,
    calculate_species_distribution,
    calculate_village_risk_summary,
    get_species_emoji,
    SYNTHETIC_DATA_NOTICE,
)


# ----------------------------------------------------------------
# Color constants (matching CSS)
# ----------------------------------------------------------------
RISK_COLORS = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}
SPECIES_COLORS = [
    "#3b82d4", "#7c5cd8", "#16a34a", "#d97706", "#dc2626", "#0891b2"
]


def _header():
    st.markdown(
        """
        <div class="wsk-header">
            <h1>🐘 Wild Shield Karnataka</h1>
            <p>Human–Wildlife Conflict Prevention System</p>
            <p class="tagline">AI-powered risk assessment & community safety advisories</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _synthetic_notice():
    st.markdown(
        '<div class="synthetic-banner">'
        '⚠️ <strong>Demo Mode:</strong> This dashboard displays synthetic demonstration data '
        'labeled <code>is_synthetic = TRUE</code>. '
        'No real wildlife locations are exposed. This system does NOT track real-time animal movements.'
        '</div>',
        unsafe_allow_html=True,
    )


def render_main_dashboard(orchestrator):
    """
    Render the main dashboard page.
    Shows KPI cards, incident trends, species distribution, village summary.
    """
    _header()
    _synthetic_notice()

    # ── Load data ────────────────────────────────────────────────
    with st.spinner("Loading dashboard data..."):
        df = orchestrator.get_all_incidents()
        stats = orchestrator.get_dashboard_stats()

    # ── KPI Cards ────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📋 Total Incidents",
            value=stats.get("total_incidents", 0),
            help="Total historical wildlife incidents in the dataset",
        )
    with col2:
        st.metric(
            label="🏘️ Villages Affected",
            value=stats.get("villages_affected", 0),
            help="Number of distinct villages with recorded incidents",
        )
    with col3:
        st.metric(
            label="🦌 Species Recorded",
            value=stats.get("species_count", 0),
            help="Number of distinct wildlife species in the dataset",
        )
    with col4:
        high = stats.get("high_risk_villages", 0)
        medium = stats.get("medium_risk_villages", 0)
        st.metric(
            label="🔴 High / 🟡 Medium Risk",
            value=f"{high} / {medium}",
            help="Villages assessed as High or Medium risk (requires running assessments first)",
        )

    st.divider()

    if df.empty:
        st.warning(
            "No incident data available. "
            "Make sure `data/synthetic/sample_incidents.csv` exists, "
            "or seed the database with `python database/seed_data.py`."
        )
        return

    # ── Charts Row 1 ─────────────────────────────────────────────
    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.subheader("📈 Monthly Incident Trend")
        trend_df = calculate_incident_trends(df)
        if not trend_df.empty:
            fig = px.line(
                trend_df,
                x="month",
                y="count",
                markers=True,
                color_discrete_sequence=["#3b82d4"],
                labels={"month": "Month", "count": "Incidents"},
            )
            fig.update_traces(
                line=dict(width=2.5),
                marker=dict(size=8, color="#3b82d4"),
            )
            fig.update_layout(
                height=280,
                margin=dict(t=10, b=30, l=0, r=0),
                xaxis_title="",
                yaxis_title="Incidents",
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(size=11),
                xaxis=dict(tickangle=-30, gridcolor="#f3f4f6"),
                yaxis=dict(gridcolor="#f3f4f6"),
            )
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("No trend data available.")

    with col_b:
        st.subheader("🦌 Species Distribution")
        species_dist = calculate_species_distribution(df)
        if species_dist:
            labels = [f"{get_species_emoji(k)} {k}" for k in species_dist.keys()]
            fig2 = go.Figure(
                data=[
                    go.Pie(
                        labels=labels,
                        values=list(species_dist.values()),
                        hole=0.42,
                        marker=dict(colors=SPECIES_COLORS),
                        textinfo="percent",
                        hoverinfo="label+value+percent",
                    )
                ]
            )
            fig2.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=0, r=0),
                showlegend=True,
                legend=dict(orientation="v", x=1.02, y=0.5, font=dict(size=10)),
                paper_bgcolor="#ffffff",
            )
            st.plotly_chart(fig2, width="stretch")

    st.divider()

    # ── Charts Row 2 ─────────────────────────────────────────────
    col_c, col_d = st.columns([2, 3])

    with col_c:
        st.subheader("📍 Incidents by District")
        if "district" in df.columns:
            district_counts = df["district"].value_counts().reset_index()
            district_counts.columns = ["district", "count"]
            fig3 = px.bar(
                district_counts,
                x="count",
                y="district",
                orientation="h",
                color="count",
                color_continuous_scale=[[0, "#d1fae5"], [0.5, "#d97706"], [1, "#dc2626"]],
                labels={"count": "Incidents", "district": ""},
            )
            fig3.update_layout(
                height=280,
                margin=dict(t=10, b=10, l=0, r=10),
                coloraxis_showscale=False,
                plot_bgcolor="#ffffff",
                paper_bgcolor="#ffffff",
                font=dict(size=11),
                xaxis=dict(gridcolor="#f3f4f6"),
            )
            st.plotly_chart(fig3, width="stretch")

    with col_d:
        st.subheader("🏘️ Village Incident Summary")
        summary = calculate_village_risk_summary(df)
        if not summary.empty:
            display_df = summary[
                ["village_name", "district", "taluk", "incident_count", "top_species"]
            ].sort_values("incident_count", ascending=False).reset_index(drop=True)
            display_df.columns = ["Village", "District", "Taluk", "Incidents", "Top Species"]
            st.dataframe(
                display_df,
                width="stretch",
                hide_index=True,
                height=280,
            )

    st.divider()

    # ── Severity breakdown ────────────────────────────────────────
    if "severity" in df.columns:
        st.subheader("⚡ Incident Severity Breakdown")
        col_e, col_f = st.columns([1, 2])

        with col_e:
            severity_counts = df["severity"].value_counts()
            total = len(df)
            for sev, color in [("HIGH", "#dc2626"), ("MEDIUM", "#d97706"), ("LOW", "#16a34a")]:
                count = severity_counts.get(sev, 0)
                pct = count / total * 100 if total > 0 else 0
                st.markdown(
                    f'<div style="margin-bottom:0.6rem">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'font-size:0.85rem;margin-bottom:3px">'
                    f'<span class="badge badge-{sev}">{sev}</span>'
                    f'<span style="color:#57606a">{count} ({pct:.0f}%)</span>'
                    f'</div>'
                    f'<div class="score-bar-track">'
                    f'<div class="score-bar-fill {sev.lower()}" style="width:{pct}%"></div>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )

        with col_f:
            st.subheader("📋 Recent Incidents (Last 10)")
            recent = df.head(10)
            cols_show = [c for c in ["incident_date", "village_name", "species", "incident_type", "severity"] if c in recent.columns]
            st.dataframe(
                recent[cols_show],
                width="stretch",
                hide_index=True,
                height=200,
            )

    # Footer
    st.markdown(
        '<div class="wsk-footer">Wild Shield Karnataka · IBM Granite + IBM Cloud · '
        'Hackathon Demo — Synthetic Data Only</div>',
        unsafe_allow_html=True,
    )
