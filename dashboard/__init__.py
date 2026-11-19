# dashboard/__init__.py
from dashboard.main_page import render_main_dashboard
from dashboard.risk_page import render_risk_dashboard
from dashboard.advisory_page import render_advisory_dashboard
from dashboard.incident_page import render_incident_history
from dashboard.agent_console_page import render_agent_console

__all__ = [
    "render_main_dashboard",
    "render_risk_dashboard",
    "render_advisory_dashboard",
    "render_incident_history",
    "render_agent_console",
]
