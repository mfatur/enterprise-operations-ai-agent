from backend.app.database.connection import get_connection


def get_orders():
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    order_date,
                    product,
                    category,
                    quantity,
                    unit_price,
                    region
                FROM orders
                ORDER BY id;
                """
            )

            rows = cursor.fetchall()

    return rows