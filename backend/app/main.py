from pathlib import Path
from fastapi.responses import FileResponse

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage

from backend.app.agents.sales_agent import sales_agent
from backend.app.tools.sales_tools import (
    get_total_revenue,
    get_total_quantity_sold,
    get_average_order_value,
    get_top_products,
    get_revenue_by_region,
)

app = FastAPI(
    title="Enterprise Operations AI Agent",
    version="1.0.0",
)

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

# =========================
# CORS
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# REQUEST MODEL
# =========================

class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="Pertanyaan untuk Sales AI Agent"
    )


# =========================
# ROOT
# =========================

@app.get("/")
def root():
    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# =========================
# CHAT
# =========================

@app.post("/chat")
def chat(request: ChatRequest):

    try:

        question = request.question.strip()

        if not question:
            raise HTTPException(
                status_code=400,
                detail="Question tidak boleh kosong."
            )

        print(f"[CHAT] Question: {question}")

        result = sales_agent.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=question
                    )
                ]
            }
        )

        final_message = result["messages"][-1]

        if isinstance(final_message.content, list):

            answer = ""

            for block in final_message.content:

                if block.get("type") == "text":
                    answer += block["text"]

        else:

            answer = final_message.content


        print(f"[CHAT] Answer: {answer}")

        return {
            "answer": answer
        }


    except HTTPException:
        raise


    except Exception as e:

        error_message = str(e)

        print(f"[ERROR] {error_message}")


        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
        ):

            raise HTTPException(
                status_code=503,
                detail=(
                    "Layanan AI sedang mencapai batas penggunaan "
                    "Gemini API. Silakan coba lagi nanti."
                )
            )


        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
        ):

            raise HTTPException(
                status_code=503,
                detail=(
                    "Model AI sedang tidak tersedia. "
                    "Silakan coba lagi beberapa saat."
                )
            )


        raise HTTPException(
            status_code=500,
            detail="Terjadi kesalahan internal pada AI Agent."
        )
    # =========================
# DASHBOARD
# =========================

@app.get("/dashboard")
def dashboard():

    try:

        total_revenue = get_total_revenue()

        total_quantity_sold = get_total_quantity_sold()

        average_order_value = get_average_order_value()

        top_products = get_top_products(
            limit=3
        )

        revenue_by_region = get_revenue_by_region()

        return {
            "total_revenue": total_revenue,
            "total_quantity_sold": total_quantity_sold,
            "average_order_value": average_order_value,
            "top_products": top_products,
            "revenue_by_region": revenue_by_region,
        }

    except Exception as e:

        print(
            f"[DASHBOARD ERROR] {str(e)}"
        )

        raise HTTPException(
            status_code=500,
            detail="Gagal mengambil data dashboard."
        )
# =========================
# FRONTEND STATIC FILES
# =========================

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="frontend",
)