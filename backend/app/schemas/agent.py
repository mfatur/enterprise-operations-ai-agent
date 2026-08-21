from datetime import date

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="User request for the AI agent"
    )

class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        description="User message for the LLM"
    )


class ChatResponse(BaseModel):
    response: str
    
class OrderResponse(BaseModel):
    id: int
    order_date: date
    product: str
    category: str
    quantity: int
    unit_price: float
    region: str