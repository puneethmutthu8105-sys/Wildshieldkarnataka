# database/__init__.py
from database.connection import get_connection, test_connection

__all__ = ["get_connection", "test_connection"]
