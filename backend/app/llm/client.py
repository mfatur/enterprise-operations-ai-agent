import os

from dotenv import load_dotenv
from google import genai

from backend.app.tools.sales_tools import (
    get_total_revenue,
    get_revenue_by_region,
)


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(
    api_key=GEMINI_API_KEY
)


def generate_response(message: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=message,
        config={
            "tools": [
                get_total_revenue,
                get_revenue_by_region,
            ],
            "system_instruction": (
                "You are an enterprise sales analysis assistant. "
                "When the user asks about actual sales data, revenue, "
                "regions, products, or orders, use the available tools "
                "to retrieve data from the database. "
                "Do not invent business data."
            ),
        },
    )

    return response.text