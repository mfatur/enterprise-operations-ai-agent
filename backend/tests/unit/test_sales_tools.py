"""Deterministic unit tests for the sales database tools."""

import sys
import types
from unittest.mock import patch

import pytest


# Prevent importing the production connection module during collection. That
# module loads environment variables, while these tests replace the connection
# boundary entirely and must not need a database or a .env file.
_connection_module = types.ModuleType("backend.app.database.connection")
_connection_module.get_connection = lambda: None
sys.modules["backend.app.database.connection"] = _connection_module

from backend.app.tools import sales_tools
from backend.tests.conftest import FakeConnection, FakeCursor


def _normalized_sql(query: str) -> str:
    return " ".join(query.split())


def _mock_connection(cursor: FakeCursor):
    return patch.object(
        sales_tools,
        "get_connection",
        return_value=FakeConnection(cursor),
    )


def test_get_total_revenue_returns_float_and_executes_expected_query():
    cursor = FakeCursor(fetchone_result=(1250.75,))

    with _mock_connection(cursor) as get_connection:
        result = sales_tools.get_total_revenue()

    assert result == 1250.75
    assert isinstance(result, float)
    get_connection.assert_called_once_with()
    assert len(cursor.executed) == 1
    query, params = cursor.executed[0]
    assert params is None
    assert _normalized_sql(query) == (
        "SELECT COALESCE( SUM(quantity * unit_price), 0 ) FROM orders;"
    )


def test_get_total_revenue_returns_zero_as_float():
    cursor = FakeCursor(fetchone_result=(0,))

    with _mock_connection(cursor):
        result = sales_tools.get_total_revenue()

    assert result == 0.0
    assert isinstance(result, float)


def test_get_revenue_by_region_maps_rows_and_converts_revenue_to_float():
    cursor = FakeCursor(
        fetchall_result=[
            ("West", 450.25),
            ("East", 300),
        ]
    )

    with _mock_connection(cursor):
        result = sales_tools.get_revenue_by_region()

    assert result == [
        {"region": "West", "revenue": 450.25},
        {"region": "East", "revenue": 300.0},
    ]
    assert all(isinstance(row["revenue"], float) for row in result)


def test_get_revenue_by_region_returns_empty_list_for_no_rows():
    cursor = FakeCursor(fetchall_result=[])

    with _mock_connection(cursor):
        result = sales_tools.get_revenue_by_region()

    assert result == []


def test_get_total_quantity_sold_returns_integer():
    cursor = FakeCursor(fetchone_result=(42,))

    with _mock_connection(cursor):
        result = sales_tools.get_total_quantity_sold()

    assert result == 42
    assert isinstance(result, int)


def test_get_total_quantity_sold_returns_zero_as_integer():
    cursor = FakeCursor(fetchone_result=(0,))

    with _mock_connection(cursor):
        result = sales_tools.get_total_quantity_sold()

    assert result == 0
    assert isinstance(result, int)


def test_get_average_order_value_returns_float():
    cursor = FakeCursor(fetchone_result=(87.5,))

    with _mock_connection(cursor):
        result = sales_tools.get_average_order_value()

    assert result == 87.5
    assert isinstance(result, float)


def test_get_average_order_value_returns_zero_as_float():
    cursor = FakeCursor(fetchone_result=(0,))

    with _mock_connection(cursor):
        result = sales_tools.get_average_order_value()

    assert result == 0.0
    assert isinstance(result, float)


def test_get_top_products_maps_rows_and_uses_default_parameterized_limit():
    cursor = FakeCursor(
        fetchall_result=[
            ("Laptop", 12),
            ("Monitor", 8),
        ]
    )

    with _mock_connection(cursor):
        result = sales_tools.get_top_products()

    assert result == [
        {"product": "Laptop", "total_quantity": 12},
        {"product": "Monitor", "total_quantity": 8},
    ]
    query, params = cursor.executed[0]
    assert "LIMIT %s;" in query
    assert params == (3,)


def test_get_top_products_uses_custom_parameterized_limit():
    cursor = FakeCursor(fetchall_result=[("Keyboard", 5)])

    with _mock_connection(cursor):
        result = sales_tools.get_top_products(limit=1)

    assert result == [{"product": "Keyboard", "total_quantity": 5}]
    assert cursor.executed[0][1] == (1,)


def test_get_top_products_returns_empty_list_for_no_rows():
    cursor = FakeCursor(fetchall_result=[])

    with _mock_connection(cursor):
        result = sales_tools.get_top_products()

    assert result == []


def test_get_top_products_by_revenue_maps_rows_and_uses_default_limit():
    cursor = FakeCursor(
        fetchall_result=[
            ("Laptop", 1000.5),
            ("Desk", 750),
        ]
    )

    with _mock_connection(cursor):
        result = sales_tools.get_top_products_by_revenue()

    assert result == [
        {"product": "Laptop", "revenue": 1000.5},
        {"product": "Desk", "revenue": 750.0},
    ]
    query, params = cursor.executed[0]
    assert "SUM(quantity * unit_price) AS revenue" in query
    assert "ORDER BY revenue DESC" in query
    assert params == (3,)


def test_get_top_products_by_revenue_uses_custom_parameterized_limit():
    cursor = FakeCursor(fetchall_result=[("Laptop", 1000)])

    with _mock_connection(cursor):
        result = sales_tools.get_top_products_by_revenue(limit=1)

    assert result == [{"product": "Laptop", "revenue": 1000.0}]
    assert cursor.executed[0][1] == (1,)


def test_get_top_products_by_revenue_returns_empty_list_for_no_rows():
    cursor = FakeCursor(fetchall_result=[])

    with _mock_connection(cursor):
        result = sales_tools.get_top_products_by_revenue()

    assert result == []


def test_get_revenue_by_category_maps_rows_and_converts_revenue_to_float():
    cursor = FakeCursor(
        fetchall_result=[
            ("Electronics", 900),
            ("Office", 125.5),
        ]
    )

    with _mock_connection(cursor):
        result = sales_tools.get_revenue_by_category()

    assert result == [
        {"category": "Electronics", "revenue": 900.0},
        {"category": "Office", "revenue": 125.5},
    ]
    assert all(isinstance(row["revenue"], float) for row in result)


def test_get_revenue_by_category_returns_empty_list_for_no_rows():
    cursor = FakeCursor(fetchall_result=[])

    with _mock_connection(cursor):
        result = sales_tools.get_revenue_by_category()

    assert result == []


def test_database_exceptions_are_propagated():
    cursor = FakeCursor(execute_error=RuntimeError("database unavailable"))

    with _mock_connection(cursor):
        with pytest.raises(RuntimeError, match="database unavailable"):
            sales_tools.get_total_revenue()
