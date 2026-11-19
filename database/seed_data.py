# ============================================================
# database/seed_data.py
# Wild Shield Karnataka — Synthetic Demo Data Loader
#
# Run this AFTER models.py to populate tables with demo data:
#   python database/seed_data.py
#
# ALL data inserted by this script has is_synthetic = TRUE.
# This clearly labels all demo data as synthetic.
# ============================================================

import csv
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection
from database.models import create_all_tables

logger = logging.getLogger(__name__)

# Synthetic village metadata for Karnataka forest-edge villages
SYNTHETIC_VILLAGES = [
    ("Nagapura",                "Hunsur",         "Mysuru",           12.2615, 76.2891,  450,  1.8),
    ("Heggadadevanakote",       "HD Kote",         "Mysuru",           11.9887, 76.3245, 1200,  2.5),
    ("Veeranahosahalli",        "Kushalnagar",     "Kodagu",           12.4582, 75.9634,  320,  0.9),
    ("Manchanabele",            "Ramanagara",      "Ramanagara",       12.7225, 77.3854,  680,  4.2),
    ("Biligirirangana Hills",   "Yelandur",        "Chamarajanagara",  11.9765, 77.1234,  290,  1.2),
    ("Chikkaballapur Village",  "Chikkaballapur",  "Chikkaballapur",   13.4320, 77.7295,  520,  3.5),
    ("Bhadra Village",          "Tarikere",        "Chikkamagaluru",   13.7115, 75.8140,  410,  1.5),
    ("Kabini Village",          "Hunsur",          "Mysuru",           11.9450, 76.3785,  280,  0.5),
    ("Nagarahole Village",      "Virajpet",        "Kodagu",           12.1680, 76.0325,  360,  1.1),
    ("Bandipur Village",        "Gundlupet",       "Chamarajanagara",  11.6710, 76.6340,  480,  0.8),
    ("Somvarpet",               "Somvarpet",       "Kodagu",           12.5985, 75.9380,  890,  3.0),
]

CSV_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "synthetic", "sample_incidents.csv"
)


def seed_villages(cursor) -> int:
    """Insert synthetic village records. Returns count inserted."""
    count = 0
    for row in SYNTHETIC_VILLAGES:
        name, taluk, district, lat, lon, population, proximity = row
        cursor.execute(
            """
            INSERT IGNORE INTO villages
                (village_name, taluk, district, latitude, longitude,
                 population, proximity_to_forest_km)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (name, taluk, district, lat, lon, population, proximity),
        )
        count += cursor.rowcount
    return count


def seed_incidents(cursor) -> int:
    """Load incidents from the synthetic CSV and insert into DB."""
    if not os.path.exists(CSV_PATH):
        print(f"  ⚠ CSV not found at {CSV_PATH}. Skipping incidents.")
        return 0

    count = 0
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute(
                """
                INSERT INTO wildlife_incidents
                    (village_name, district, taluk, latitude, longitude,
                     species, incident_type, severity, description,
                     incident_date, reported_by, is_verified, is_synthetic)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    row["village_name"],
                    row["district"],
                    row["taluk"],
                    float(row["latitude"]),
                    float(row["longitude"]),
                    row["species"],
                    row["incident_type"],
                    row["severity"],
                    row["description"],
                    row["incident_date"],
                    row["reported_by"],
                    row["is_verified"].upper() == "TRUE",
                    True,  # Always is_synthetic = TRUE for demo data
                ),
            )
            count += 1
    return count


def run_seed() -> bool:
    """Main seeding function. Returns True on success."""
    conn = get_connection()
    if conn is None:
        print("ERROR: Cannot connect to MySQL. Check your .env configuration.")
        return False

    cursor = conn.cursor()
    try:
        v_count = seed_villages(cursor)
        print(f"  ✓ Inserted {v_count} village record(s).")

        i_count = seed_incidents(cursor)
        print(f"  ✓ Inserted {i_count} synthetic incident record(s).")

        conn.commit()
        print(f"\n  ⚠ REMINDER: All {i_count} incidents are labeled is_synthetic = TRUE.")
        print("  These are demonstration records only — not real wildlife incidents.")
        return True
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ Seeding failed: {exc}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\n🌱 Wild Shield Karnataka — Synthetic Data Seeder")
    print("=" * 50)
    print("Creating tables if not present...")
    create_all_tables()
    print("\nLoading synthetic demonstration data...")
    if run_seed():
        print("\n✅ Synthetic data loaded successfully.")
        print("Run 'streamlit run app.py' to start the application.")
    else:
        print("\n❌ Seeding failed. See errors above.")
    print()
