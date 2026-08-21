from fastapi import FastAPI
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from backend.app.agents.sales_agent import sales_agent


app = FastAPI(
    title="Enterprise Operations AI Agent",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "Enterprise Operations AI Agent is running"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    result = sales_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content=request.question
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

    return {
        "answer": answer
    }