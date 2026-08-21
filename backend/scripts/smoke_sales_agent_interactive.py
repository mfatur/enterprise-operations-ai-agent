from langchain_core.messages import HumanMessage

from backend.app.agents.sales_agent import sales_agent


print("\n=== SALES AI AGENT ===")

question = input("\nPertanyaan: ")

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

print("\nJawaban:")

if isinstance(final_message.content, list):
    for block in final_message.content:
        if block.get("type") == "text":
            print(block["text"])
else:
    print(final_message.content)