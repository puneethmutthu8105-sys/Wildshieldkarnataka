# ============================================================
# config/settings.py
# Wild Shield Karnataka — Configuration Loader
#
# This module loads all environment variables and provides
# typed configuration objects for the rest of the application.
# It supports both local .env files and Streamlit Cloud Secrets.
# ============================================================

import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file for local development
# In Streamlit Cloud, secrets are injected by the platform
load_dotenv()


def _get(key: str, default: str = "") -> str:
    """
    Get a configuration value.
    Checks Streamlit secrets first (production), then environment variables (local dev).
    """
    try:
        import streamlit as st
        return st.secrets.get(key, os.environ.get(key, default))
    except Exception:
        return os.environ.get(key, default)


# ----------------------------------------------------------------
# LLM Configuration — Agent 1 (Risk Assessment)
# ----------------------------------------------------------------
@dataclass
class LLMConfig1:
    """Configuration for IBM Granite LLM used by Agent 1."""
    api_key: str
    project_id: str
    model_id: str
    url: str
    # Analytical tasks — low temperature for consistent, factual output
    temperature: float = 0.2
    max_new_tokens: int = 1024
    top_p: float = 0.9


# ----------------------------------------------------------------
# LLM Configuration — Agent 2 (Safety Advisor — Replicate)
# ----------------------------------------------------------------
@dataclass
class LLMConfig2:
    """
    Configuration for Agent 2 — uses Replicate API with IBM Granite.
    Model: ibm-granite/granite-4.2-8b on Replicate.
    No project_id or Watsonx URL needed — Replicate uses only an API token.
    """
    api_key: str                 # Replicate API token (REPLICATE_API_KEY)
    model_id: str                # e.g. "ibm-granite/granite-4.2-8b"
    # Replicate uses a different parameter name scheme
    temperature: float = 0.7
    max_new_tokens: int = 1500
    top_p: float = 0.95


# ----------------------------------------------------------------
# Database Configuration
# ----------------------------------------------------------------
@dataclass
class DatabaseConfig:
    """MySQL database connection configuration."""
    host: str
    port: int
    name: str
    user: str
    password: str


# ----------------------------------------------------------------
# Application Configuration
# ----------------------------------------------------------------
@dataclass
class AppConfig:
    """General application configuration."""
    env: str
    debug: bool
    log_level: str


# ----------------------------------------------------------------
# Configuration Factory — builds typed config objects from env
# ----------------------------------------------------------------
def get_llm_config_1() -> LLMConfig1:
    """Return LLM configuration for Agent 1."""
    return LLMConfig1(
        api_key=_get("WATSONX_API_KEY_1"),
        project_id=_get("WATSONX_PROJECT_ID_1"),
        model_id=_get("WATSONX_MODEL_ID_1", "ibm/granite-13b-instruct-v2"),
        url=_get("WATSONX_URL_1", "https://us-south.ml.cloud.ibm.com"),
    )


def get_llm_config_2() -> LLMConfig2:
    """Return LLM configuration for Agent 2 (Replicate)."""
    return LLMConfig2(
        api_key=_get("REPLICATE_API_KEY"),
        model_id=_get("REPLICATE_MODEL_ID", "ibm-granite/granite-4.2-8b"),
    )


def get_db_config() -> DatabaseConfig:
    """Return database configuration."""
    return DatabaseConfig(
        host=_get("DB_HOST", "localhost"),
        port=int(_get("DB_PORT", "3306")),
        name=_get("DB_NAME", "wildshield_karnataka"),
        user=_get("DB_USER", "root"),
        password=_get("DB_PASSWORD", ""),
    )


def get_app_config() -> AppConfig:
    """Return application configuration."""
    return AppConfig(
        env=_get("APP_ENV", "development"),
        debug=_get("APP_DEBUG", "false").lower() == "true",
        log_level=_get("LOG_LEVEL", "INFO"),
    )


def validate_config() -> dict:
    """
    Validate that all required configuration values are present.
    Returns a dict with 'valid' bool and 'errors' list.
    Used on startup to give clear error messages.
    """
    errors = []
    cfg1 = get_llm_config_1()
    cfg2 = get_llm_config_2()
    db = get_db_config()

    if not cfg1.api_key or cfg1.api_key.startswith("REPLACE"):
        errors.append("WATSONX_API_KEY_1 is not configured (Agent 1 — IBM Watsonx).")
    if not cfg1.project_id or cfg1.project_id.startswith("REPLACE"):
        errors.append("WATSONX_PROJECT_ID_1 is not configured (Agent 1 — IBM Watsonx).")
    if not cfg2.api_key or cfg2.api_key.startswith("REPLACE"):
        errors.append("REPLICATE_API_KEY is not configured (Agent 2 — Replicate).")
    # DB is optional — app runs in CSV demo mode without it, so no error raised.

    return {"valid": len(errors) == 0, "errors": errors}
