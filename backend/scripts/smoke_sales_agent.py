from langchain_core.messages import HumanMessage

from backend.app.agents.sales_agent import sales_agent


result = sales_agent.invoke(
    {
        "messages": [
            HumanMessage(
                content="Berapa total revenue?"
            )
        ]
    }
)


for message in result["messages"]:
    print("\n--- MESSAGE ---")
    print(message)