# ============================================================
# database/models.py
# Wild Shield Karnataka — Database Schema & Table Creation
#
# Run this script directly to create all tables:
#   python database/models.py
# ============================================================

import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_connection

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------
# SQL Statements — Table Definitions
# ----------------------------------------------------------------

CREATE_VILLAGES_TABLE = """
CREATE TABLE IF NOT EXISTS villages (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    village_name            VARCHAR(100) NOT NULL,
    taluk                   VARCHAR(100),
    district                VARCHAR(100),
    latitude                DECIMAL(10, 7),
    longitude               DECIMAL(10, 7),
    population              INT,
    proximity_to_forest_km  DECIMAL(5, 2),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_village_name  (village_name),
    INDEX idx_district      (district)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_WILDLIFE_INCIDENTS_TABLE = """
CREATE TABLE IF NOT EXISTS wildlife_incidents (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    village_name    VARCHAR(100) NOT NULL,
    district        VARCHAR(100),
    taluk           VARCHAR(100),
    latitude        DECIMAL(10, 7),
    longitude       DECIMAL(10, 7),
    species         VARCHAR(100) NOT NULL,
    incident_type   VARCHAR(100),
    severity        ENUM('LOW', 'MEDIUM', 'HIGH') DEFAULT 'MEDIUM',
    description     TEXT,
    incident_date   DATE NOT NULL,
    reported_by     VARCHAR(100),
    is_verified     BOOLEAN DEFAULT FALSE,
    is_synthetic    BOOLEAN DEFAULT TRUE COMMENT 'TRUE = synthetic demo data',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_village   (village_name),
    INDEX idx_species   (species),
    INDEX idx_date      (incident_date),
    INDEX idx_district  (district)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_RISK_ASSESSMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS risk_assessments (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    village_name        VARCHAR(100) NOT NULL,
    district            VARCHAR(100),
    risk_score          DECIMAL(5, 2),
    risk_level          ENUM('LOW', 'MEDIUM', 'HIGH', 'UNKNOWN') DEFAULT 'UNKNOWN',
    incident_count      INT DEFAULT 0,
    primary_species     JSON,
    risk_factors        JSON,
    analysis_summary    TEXT,
    assessed_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent1_model_used   VARCHAR(100),
    INDEX idx_village   (village_name),
    INDEX idx_risk_level (risk_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_SAFETY_ADVISORIES_TABLE = """
CREATE TABLE IF NOT EXISTS safety_advisories (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    risk_assessment_id  INT,
    village_name        VARCHAR(100) NOT NULL,
    district            VARCHAR(100),
    advisory_en         TEXT,
    advisory_kn         TEXT COMMENT 'Kannada language advisory',
    priority            ENUM('URGENT', 'CAUTION', 'AWARENESS') DEFAULT 'CAUTION',
    target_audience     JSON,
    precautions         JSON,
    generated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent2_model_used   VARCHAR(100),
    FOREIGN KEY (risk_assessment_id) REFERENCES risk_assessments(id)
        ON DELETE SET NULL,
    INDEX idx_village   (village_name),
    INDEX idx_priority  (priority)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

CREATE_FOREST_BOUNDARIES_TABLE = """
CREATE TABLE IF NOT EXISTS forest_boundaries (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    boundary_name   VARCHAR(200) NOT NULL,
    geojson_data    LONGTEXT,
    district        VARCHAR(100),
    reserve_type    VARCHAR(100) COMMENT 'e.g. National Park, Wildlife Sanctuary',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

ALL_TABLES = [
    ("villages", CREATE_VILLAGES_TABLE),
    ("wildlife_incidents", CREATE_WILDLIFE_INCIDENTS_TABLE),
    ("risk_assessments", CREATE_RISK_ASSESSMENTS_TABLE),
    ("safety_advisories", CREATE_SAFETY_ADVISORIES_TABLE),
    ("forest_boundaries", CREATE_FOREST_BOUNDARIES_TABLE),
]


def create_all_tables() -> bool:
    """
    Create all required database tables.
    Safe to run multiple times — uses CREATE TABLE IF NOT EXISTS.
    Returns True on success, False on failure.
    """
    conn = get_connection()
    if conn is None:
        print("ERROR: Could not connect to MySQL. Check your .env configuration.")
        return False

    cursor = conn.cursor()
    success = True

    for table_name, sql in ALL_TABLES:
        try:
            cursor.execute(sql)
            print(f"  ✓ Table '{table_name}' created (or already exists).")
        except Exception as exc:
            print(f"  ✗ Failed to create table '{table_name}': {exc}")
            success = False

    conn.commit()
    cursor.close()
    conn.close()
    return success


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("\n🗄️  Wild Shield Karnataka — Database Setup")
    print("=" * 50)
    if create_all_tables():
        print("\n✅ All tables created successfully.")
        print("Next step: Run 'python database/seed_data.py' to load synthetic data.")
    else:
        print("\n❌ Table creation failed. Check the error messages above.")
    print()
