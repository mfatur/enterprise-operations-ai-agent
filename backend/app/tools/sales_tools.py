import logging

from backend.app.database.connection import get_connection


logger = logging.getLogger(__name__)


def get_total_revenue() -> float:
    """Get the total revenue from all orders in the database."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(quantity * unit_price),
                    0
                )
                FROM orders;
                """
            )

            result = cursor.fetchone()

    revenue = float(result[0])

    logger.info(
        "Tool get_total_revenue completed: %s",
        revenue
    )

    return revenue


def get_revenue_by_region() -> list[dict]:
    """Get total revenue grouped by sales region."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    region,
                    SUM(quantity * unit_price) AS revenue
                FROM orders
                GROUP BY region
                ORDER BY revenue DESC;
                """
            )

            rows = cursor.fetchall()

    logger.info(
        "Tool get_revenue_by_region completed: %d regions",
        len(rows)
    )

    return [
        {
            "region": row[0],
            "revenue": float(row[1]),
        }
        for row in rows
    ]


def get_total_quantity_sold() -> int:
    """Get the total quantity of products sold."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(quantity),
                    0
                )
                FROM orders;
                """
            )

            result = cursor.fetchone()

    quantity = int(result[0])

    logger.info(
        "Tool get_total_quantity_sold completed: %s",
        quantity
    )

    return quantity


def get_average_order_value() -> float:
    """Get the average revenue per order."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(
                    SUM(quantity * unit_price)
                    / NULLIF(COUNT(DISTINCT id), 0),
                    0
                )
                FROM orders;
                """
            )

            result = cursor.fetchone()

    average_order_value = float(result[0])

    logger.info(
        "Tool get_average_order_value completed: %s",
        average_order_value
    )

    return average_order_value


def get_top_products(limit: int = 3) -> list[dict]:
    """Get the top selling products by total quantity sold."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    product,
                    SUM(quantity) AS total_quantity
                FROM orders
                GROUP BY product
                ORDER BY total_quantity DESC
                LIMIT %s;
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    logger.info(
        "Tool get_top_products completed: %d products",
        len(rows)
    )

    return [
        {
            "product": row[0],
            "total_quantity": int(row[1]),
        }
        for row in rows
    ]


def get_top_products_by_revenue(limit: int = 3) -> list[dict]:
    """Get the top products by total revenue."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    product,
                    SUM(quantity * unit_price) AS revenue
                FROM orders
                GROUP BY product
                ORDER BY revenue DESC
                LIMIT %s;
                """,
                (limit,),
            )

            rows = cursor.fetchall()

    logger.info(
        "Tool get_top_products_by_revenue completed: %d products",
        len(rows)
    )

    return [
        {
            "product": row[0],
            "revenue": float(row[1]),
        }
        for row in rows
    ]


def get_revenue_by_category() -> list[dict]:
    """Get total revenue grouped by product category."""

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    category,
                    SUM(quantity * unit_price) AS revenue
                FROM orders
                GROUP BY category
                ORDER BY revenue DESC;
                """
            )

            rows = cursor.fetchall()

    logger.info(
        "Tool get_revenue_by_category completed: %d categories",
        len(rows)
    )

    return [
        {
            "category": row[0],
            "revenue": float(row[1]),
        }
        for row in rows
    ]
