"""Opt-in PostgreSQL integration tests for the real sales-tool SQL queries."""

import os
import uuid
from dataclasses import dataclass

import psycopg
import pytest
from psycopg import sql


pytestmark = [pytest.mark.integration, pytest.mark.database]


TEST_DATABASE_URL = os.getenv("SALES_AGENT_TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    pytest.skip(
        "SALES_AGENT_TEST_DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )

try:
    _connection_info = psycopg.conninfo.conninfo_to_dict(TEST_DATABASE_URL)
except psycopg.ProgrammingError:
    pytest.skip(
        "SALES_AGENT_TEST_DATABASE_URL is not a valid PostgreSQL connection string",
        allow_module_level=True,
    )

_database_name = _connection_info.get("dbname", "")
if "test" not in _database_name.lower():
    pytest.skip(
        "SALES_AGENT_TEST_DATABASE_URL must identify a dedicated test database",
        allow_module_level=True,
    )


# The shared test configuration supplies an import-safe placeholder for the
# production connection module. This import executes the real sales-tool SQL,
# while the fixture below replaces only its connection factory.
from backend.app.tools import sales_tools


@dataclass
class IsolatedDatabase:
    schema_name: str
    admin_connection: psycopg.Connection


@pytest.fixture
def isolated_database(monkeypatch):
    """Create and remove a per-test schema in the explicitly supplied test DB."""

    schema_name = f"sales_tools_integration_{uuid.uuid4().hex}"
    admin_connection = psycopg.connect(TEST_DATABASE_URL, autocommit=True)
    database = IsolatedDatabase(schema_name, admin_connection)

    try:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema_name))
            )
            cursor.execute(
                sql.SQL(
                    """
                    CREATE TABLE {}.orders (
                        id INTEGER PRIMARY KEY,
                        order_date DATE NOT NULL,
                        product TEXT NOT NULL,
                        category TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        unit_price NUMERIC NOT NULL,
                        region TEXT NOT NULL
                    )
                    """
                ).format(sql.Identifier(schema_name))
            )
            cursor.executemany(
                sql.SQL(
                    """
                    INSERT INTO {}.orders
                        (id, order_date, product, category, quantity, unit_price, region)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                ).format(sql.Identifier(schema_name)),
                [
                    (1, "2026-01-01", "Laptop", "Electronics", 2, 100, "North"),
                    (2, "2026-01-02", "Laptop", "Electronics", 3, 100, "North"),
                    (3, "2026-01-03", "Desk", "Furniture", 1, 250, "South"),
                    (4, "2026-01-04", "Monitor", "Electronics", 4, 50, "East"),
                ],
            )

        def get_test_connection():
            connection = psycopg.connect(TEST_DATABASE_URL)
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("SET search_path TO {}").format(
                        sql.Identifier(schema_name)
                    )
                )
            return connection

        monkeypatch.setattr(sales_tools, "get_connection", get_test_connection)
        yield database
    finally:
        with admin_connection.cursor() as cursor:
            cursor.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                    sql.Identifier(schema_name)
                )
            )
        admin_connection.close()


def test_total_revenue_uses_real_postgresql_aggregation(isolated_database):
    assert sales_tools.get_total_revenue() == 950.0


def test_revenue_by_region_uses_real_grouping_and_ordering(isolated_database):
    assert sales_tools.get_revenue_by_region() == [
        {"region": "North", "revenue": 500.0},
        {"region": "South", "revenue": 250.0},
        {"region": "East", "revenue": 200.0},
    ]


def test_total_quantity_sold_uses_real_postgresql_aggregation(isolated_database):
    assert sales_tools.get_total_quantity_sold() == 10


def test_average_order_value_uses_revenue_per_distinct_order(isolated_database):
    assert sales_tools.get_average_order_value() == 237.5


def test_top_products_uses_real_ordering_and_requested_limit(isolated_database):
    assert sales_tools.get_top_products(limit=2) == [
        {"product": "Laptop", "total_quantity": 5},
        {"product": "Monitor", "total_quantity": 4},
    ]


def test_top_products_by_revenue_uses_real_revenue_ordering_and_limit(
    isolated_database,
):
    assert sales_tools.get_top_products_by_revenue(limit=2) == [
        {"product": "Laptop", "revenue": 500.0},
        {"product": "Desk", "revenue": 250.0},
    ]


def test_revenue_by_category_uses_real_grouping_and_ordering(isolated_database):
    assert sales_tools.get_revenue_by_category() == [
        {"category": "Electronics", "revenue": 700.0},
        {"category": "Furniture", "revenue": 250.0},
    ]


def test_sales_tools_return_current_empty_table_results(isolated_database):
    with isolated_database.admin_connection.cursor() as cursor:
        cursor.execute(
            sql.SQL("DELETE FROM {}.orders").format(
                sql.Identifier(isolated_database.schema_name)
            )
        )

    assert sales_tools.get_total_revenue() == 0.0
    assert sales_tools.get_total_quantity_sold() == 0
    assert sales_tools.get_average_order_value() == 0.0
    assert sales_tools.get_revenue_by_region() == []
    assert sales_tools.get_top_products() == []
    assert sales_tools.get_top_products_by_revenue() == []
    assert sales_tools.get_revenue_by_category() == []
