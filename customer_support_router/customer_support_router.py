import os
import getpass
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    department: str

def triage_node(state: State) -> dict:
    last_message = state["messages"][-1].content
    prompt = f"""
    Analyze this customer message and classify it into one of these 3 categories ONLY:
    'billing', 'tech', or 'sales'. Reply with just the category name in lowercase.
    
    Message: {last_message}
    """
    department = llm.invoke(prompt).content.strip().lower()
    print(f"\n🕵️ [Triage Node] Classified as: {department.upper()} department\n")
    return {"department": department}

def billing_node(state: State) -> dict:
    return {"messages": ["Hello from Billing Team!"]}

def tech_node(state: State) -> dict:
    return {"messages": ["Hello from Tech Support Team!"]}

def sales_node(state: State) -> dict:
    return {"messages": ["Hello from Sales Team!"]}

def route_to_department(state: State) -> str:
    return state["department"]

builder = StateGraph(State)

builder.add_node("triage", triage_node)
builder.add_node("billing", billing_node)
builder.add_node("tech", tech_node)
builder.add_node("sales", sales_node)

builder.add_edge(START, "triage")
builder.add_conditional_edges("triage", route_to_department, {"billing": "billing", "tech": "tech", "sales": "sales"})
builder.add_edge("billing", END)
builder.add_edge("tech", END)
builder.add_edge("sales", END)

graph = builder.compile()

if __name__ == "__main__":
    print("--- TESTING TECH ISSUE ---")
    result1 = graph.invoke({"messages": [HumanMessage(content="My screen is totally black!")]})
    print(result1["messages"][-1].content)

    print("\n--- TESTING BILLING ISSUE ---")
    result2 = graph.invoke({"messages": [HumanMessage(content="I was charged twice!")]})
    print(result2["messages"][-1].content)
