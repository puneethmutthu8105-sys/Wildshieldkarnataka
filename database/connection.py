# ============================================================
# database/connection.py
# Wild Shield Karnataka — MySQL Connection Handler
# ============================================================

import logging
import mysql.connector
from mysql.connector import Error as MySQLError

from config.settings import get_db_config

logger = logging.getLogger(__name__)


def get_connection():
    """
    Create and return a MySQL database connection.
    Returns None if the connection fails (non-fatal — app falls back to CSV).
    """
    cfg = get_db_config()
    try:
        conn = mysql.connector.connect(
            host=cfg.host,
            port=cfg.port,
            database=cfg.name,
            user=cfg.user,
            password=cfg.password,
            connection_timeout=10,
            autocommit=False,
        )
        if conn.is_connected():
            logger.debug("MySQL connection established.")
            return conn
    except MySQLError as exc:
        logger.warning("MySQL connection failed: %s", exc)
        return None


def test_connection() -> dict:
    """
    Test the database connection and return a status dict.
    Used by the dashboard to show DB connectivity status.
    """
    cfg = get_db_config()
    try:
        conn = get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return {
                "connected": True,
                "host": cfg.host,
                "database": cfg.name,
                "version": version,
                "error": None,
            }
        return {
            "connected": False,
            "host": cfg.host,
            "database": cfg.name,
            "version": None,
            "error": "Connection returned None.",
        }
    except Exception as exc:
        return {
            "connected": False,
            "host": cfg.host,
            "database": cfg.name,
            "version": None,
            "error": str(exc),
        }
