from backend.app.database.connection import get_connection

connection = get_connection()

try:
    cursor = connection.cursor()

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'orders'
        ORDER BY ordinal_position;
    """)

    rows = cursor.fetchall()

    print("=== COLUMNS TABLE ORDERS ===")

    for row in rows:
        print(f"- {row[0]} ({row[1]})")

finally:
    connection.close()