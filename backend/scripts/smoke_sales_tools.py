from backend.app.tools.sales_tools import (
    get_total_revenue,
    get_revenue_by_region,
    get_total_quantity_sold,
    get_average_order_value,
    get_top_products,
    get_revenue_by_category,
)


print("=== SALES TOOLS TEST ===")

print("\n1. Total Revenue")
print(get_total_revenue())

print("\n2. Revenue by Region")
print(get_revenue_by_region())

print("\n3. Total Quantity Sold")
print(get_total_quantity_sold())

print("\n4. Average Order Value")
print(get_average_order_value())

print("\n5. Top Products")
print(get_top_products())

print("\n6. Revenue by Category")
print(get_revenue_by_category())

print("\n=== ALL TOOLS EXECUTED ===")