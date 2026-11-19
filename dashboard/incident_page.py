# ============================================================
# dashboard/incident_page.py
# Wild Shield Karnataka — Incident History (Full Implementation)
# ============================================================

import streamlit as st
import pandas as pd
import plotly.express as px

from utils.helpers import get_species_emoji


def render_incident_history(orchestrator):
    """
    Render the historical incident management page.
    Allows filtering by location, species, severity, and date range.
    """
    st.title("📋 Historical Incident Records")
    st.markdown(
        "Browse and filter historical wildlife incident records used for risk analysis."
    )
    st.markdown(
        '<div class="synthetic-banner">'
        '⚠️ <strong>Demo Data:</strong> All records below are synthetic demonstration data '
        '(<code>is_synthetic = TRUE</code>). These are NOT real wildlife incidents.'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── Load data ────────────────────────────────────────────────
    with st.spinner("Loading incidents..."):
        df = orchestrator.get_all_incidents()

    if df.empty:
        st.warning("No incident records found. Check your data source.")
        return

    # Normalize date column
    if "incident_date" in df.columns:
        df["incident_date"] = pd.to_datetime(df["incident_date"], errors="coerce")

    # ── Filters ──────────────────────────────────────────────────
    st.subheader("🔍 Filters")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        species_options = ["All"] + sorted(df["species"].dropna().unique().tolist())
        selected_species = st.selectbox("Species:", species_options)

    with col2:
        village_options = ["All"] + sorted(df["village_name"].dropna().unique().tolist())
        selected_village = st.selectbox("Village:", village_options)

    with col3:
        district_options = ["All"] + sorted(df["district"].dropna().unique().tolist()) if "district" in df.columns else ["All"]
        selected_district = st.selectbox("District:", district_options)

    with col4:
        severity_options = ["All", "HIGH", "MEDIUM", "LOW"]
        selected_severity = st.selectbox("Severity:", severity_options)

    # Date range filter
    if "incident_date" in df.columns:
        col_d1, col_d2 = st.columns(2)
        valid_dates = df["incident_date"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
            with col_d1:
                start_date = st.date_input("From:", value=min_date, min_value=min_date, max_value=max_date)
            with col_d2:
                end_date = st.date_input("To:", value=max_date, min_value=min_date, max_value=max_date)
        else:
            start_date = end_date = None
    else:
        start_date = end_date = None

    # ── Apply filters ─────────────────────────────────────────────
    filtered_df = df.copy()

    if selected_species != "All":
        filtered_df = filtered_df[filtered_df["species"] == selected_species]
    if selected_village != "All":
        filtered_df = filtered_df[filtered_df["village_name"] == selected_village]
    if selected_district != "All" and "district" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["district"] == selected_district]
    if selected_severity != "All" and "severity" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["severity"] == selected_severity]
    if start_date and end_date and "incident_date" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["incident_date"].dt.date >= start_date) &
            (filtered_df["incident_date"].dt.date <= end_date)
        ]

    # ── Summary stats for filtered results ───────────────────────
    st.divider()

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("Filtered Incidents", len(filtered_df))
    with col_s2:
        villages_count = filtered_df["village_name"].nunique() if not filtered_df.empty else 0
        st.metric("Villages", villages_count)
    with col_s3:
        species_count = filtered_df["species"].nunique() if not filtered_df.empty else 0
        st.metric("Species", species_count)
    with col_s4:
        high_count = len(filtered_df[filtered_df["severity"] == "HIGH"]) if "severity" in filtered_df.columns else 0
        st.metric("HIGH Severity", high_count)

    # ── Mini chart for filtered data ──────────────────────────────
    if not filtered_df.empty and len(filtered_df) > 1:
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            if "species" in filtered_df.columns:
                sp_counts = filtered_df["species"].value_counts().head(8).reset_index()
                sp_counts.columns = ["species", "count"]
                sp_counts["label"] = sp_counts["species"].apply(
                    lambda x: f"{get_species_emoji(x)} {x}"
                )
                fig = px.bar(
                    sp_counts, x="count", y="label", orientation="h",
                    color="count",
                    color_continuous_scale=[[0, "#d1fae5"], [1, "#dc2626"]],
                    labels={"count": "Incidents", "label": ""},
                )
                fig.update_layout(
                    height=200,
                    margin=dict(t=5, b=10, l=0, r=0),
                    coloraxis_showscale=False,
                    plot_bgcolor="#ffffff",
                    paper_bgcolor="#ffffff",
                    font=dict(size=10),
                )
                st.plotly_chart(fig, width="stretch")

        with col_chart2:
            if "severity" in filtered_df.columns:
                sev_counts = filtered_df["severity"].value_counts().reset_index()
                sev_counts.columns = ["severity", "count"]
                sev_color_map = {"HIGH": "#dc2626", "MEDIUM": "#d97706", "LOW": "#16a34a"}
                fig2 = px.pie(
                    sev_counts, names="severity", values="count",
                    color="severity",
                    color_discrete_map=sev_color_map,
                    hole=0.4,
                )
                fig2.update_layout(
                    height=200,
                    margin=dict(t=5, b=5, l=0, r=0),
                    showlegend=True,
                    paper_bgcolor="#ffffff",
                    font=dict(size=10),
                    legend=dict(font=dict(size=9)),
                )
                st.plotly_chart(fig2, width="stretch")

    st.divider()

    # ── Data table ────────────────────────────────────────────────
    if filtered_df.empty:
        st.info("No incidents match the selected filters.")
        return

    st.subheader(f"📋 Showing {len(filtered_df)} incident(s)")

    # Choose columns to display
    display_cols = [
        "incident_date", "village_name", "district", "taluk",
        "species", "incident_type", "severity", "description",
        "reported_by", "is_verified", "is_synthetic",
    ]
    available_cols = [c for c in display_cols if c in filtered_df.columns]

    display_df = filtered_df[available_cols].copy()
    if "incident_date" in display_df.columns:
        display_df["incident_date"] = display_df["incident_date"].dt.strftime("%Y-%m-%d")
    display_df = display_df.sort_values(
        "incident_date" if "incident_date" in display_df.columns else display_df.columns[0],
        ascending=False
    ).reset_index(drop=True)

    # Rename columns for display
    rename_map = {
        "incident_date": "Date",
        "village_name": "Village",
        "district": "District",
        "taluk": "Taluk",
        "species": "Species",
        "incident_type": "Type",
        "severity": "Severity",
        "description": "Description",
        "reported_by": "Reported By",
        "is_verified": "Verified",
        "is_synthetic": "Synthetic",
    }
    display_df.rename(columns={k: v for k, v in rename_map.items() if k in display_df.columns}, inplace=True)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=400,
    )

    # Download button
    csv = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download filtered data as CSV",
        data=csv,
        file_name=f"wildshield_incidents_filtered.csv",
        mime="text/csv",
    )
