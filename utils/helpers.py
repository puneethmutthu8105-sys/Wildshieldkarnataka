# ============================================================
# utils/helpers.py
# Wild Shield Karnataka — Shared Utility Functions
# ============================================================

from __future__ import annotations
import pandas as pd
from typing import Any


# ----------------------------------------------------------------
# Display Formatting
# ----------------------------------------------------------------

RISK_COLORS = {
    "HIGH": "#dc2626",    # Red
    "MEDIUM": "#d97706",  # Amber
    "LOW": "#16a34a",     # Green
    "UNKNOWN": "#6b7280", # Gray
}

PRIORITY_COLORS = {
    "URGENT": "#dc2626",
    "CAUTION": "#d97706",
    "AWARENESS": "#16a34a",
}

SPECIES_EMOJIS = {
    "elephant": "🐘",
    "leopard": "🐆",
    "tiger": "🐅",
    "wild boar": "🐗",
    "gaur": "🐃",
    "bear": "🐻",
    "sloth bear": "🐻",
}


def get_risk_color(risk_level: str) -> str:
    """Return hex color for a given risk level."""
    return RISK_COLORS.get(risk_level.upper(), RISK_COLORS["UNKNOWN"])


def get_priority_color(priority: str) -> str:
    """Return hex color for an advisory priority."""
    return PRIORITY_COLORS.get(priority.upper(), PRIORITY_COLORS["CAUTION"])


def format_risk_badge(risk_level: str) -> str:
    """Return an HTML badge string for display in Streamlit markdown."""
    color = get_risk_color(risk_level)
    return (
        f'<span style="background-color:{color};color:white;'
        f'padding:3px 10px;border-radius:12px;font-weight:bold;'
        f'font-size:0.85rem;">{risk_level}</span>'
    )


def format_priority_badge(priority: str) -> str:
    """Return an HTML badge string for advisory priority."""
    color = get_priority_color(priority)
    return (
        f'<span style="background-color:{color};color:white;'
        f'padding:3px 10px;border-radius:12px;font-weight:bold;'
        f'font-size:0.85rem;">{priority}</span>'
    )


def get_species_emoji(species: str) -> str:
    """Return an emoji for a wildlife species name."""
    return SPECIES_EMOJIS.get(species.lower(), "🦌")


# ----------------------------------------------------------------
# Data Processing
# ----------------------------------------------------------------

def calculate_incident_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate monthly incident counts for trend charts.
    Expects a 'incident_date' column in the DataFrame.
    Returns a DataFrame with columns: month, count.
    """
    if df.empty or "incident_date" not in df.columns:
        return pd.DataFrame(columns=["month", "count"])

    df = df.copy()
    df["incident_date"] = pd.to_datetime(df["incident_date"])
    monthly = (
        df.groupby(df["incident_date"].dt.to_period("M"))
        .size()
        .reset_index(name="count")
    )
    monthly["month"] = monthly["incident_date"].astype(str)
    return monthly[["month", "count"]]


def calculate_species_distribution(df: pd.DataFrame) -> dict[str, int]:
    """
    Count incidents per species.
    Returns a dict: {species_name: count}.
    """
    if df.empty or "species" not in df.columns:
        return {}
    return df["species"].value_counts().to_dict()


def calculate_village_risk_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize incident counts per village with top species.
    Returns a DataFrame with village_name, incident_count, top_species, district.
    """
    if df.empty:
        return pd.DataFrame()

    summary = (
        df.groupby("village_name")
        .agg(
            incident_count=("village_name", "count"),
            district=("district", "first"),
            taluk=("taluk", "first"),
        )
        .reset_index()
    )

    # Add top species per village
    top_species = (
        df.groupby("village_name")["species"]
        .agg(lambda x: x.value_counts().index[0] if len(x) > 0 else "Unknown")
        .reset_index()
        .rename(columns={"species": "top_species"})
    )

    return summary.merge(top_species, on="village_name", how="left")


def prepare_map_data(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Prepare incident data for map visualization.
    Returns a list of dicts with lat, lon, village, species, severity, date.
    """
    if df.empty:
        return []

    required = ["latitude", "longitude", "village_name", "species", "severity", "incident_date"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        return []

    valid = df[df["latitude"].notna() & df["longitude"].notna()].copy()
    return valid[required].to_dict(orient="records")


# ----------------------------------------------------------------
# Data Disclaimer
# ----------------------------------------------------------------

SYNTHETIC_DATA_NOTICE = (
    "⚠️ **Data Notice:** This dashboard displays **synthetic demonstration data** "
    "created for hackathon purposes. All incidents are labeled `is_synthetic = TRUE`. "
    "This system does **not** track real-time wildlife locations or movements."
)
