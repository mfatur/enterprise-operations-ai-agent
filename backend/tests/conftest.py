"""Shared fakes for isolated database-backed unit tests."""

import sys
import types


# Production connection setup loads environment variables at import time. Tests
# replace that boundary, so prevent importing it during pytest collection.
_connection_module = types.ModuleType("backend.app.database.connection")
_connection_module.get_connection = lambda: None
sys.modules["backend.app.database.connection"] = _connection_module


class FakeCursor:
    """In-memory cursor fake that records executed statements."""

    def __init__(self, *, fetchone_result=None, fetchall_result=None, execute_error=None):
        self.fetchone_result = fetchone_result
        self.fetchall_result = fetchall_result if fetchall_result is not None else []
        self.execute_error = execute_error
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


class FakeConnection:
    """In-memory connection fake compatible with nested ``with`` blocks."""

    def __init__(self, cursor):
        self.fake_cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def cursor(self):
        return self.fake_cursor
