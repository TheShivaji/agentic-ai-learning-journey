import os
import getpass
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google API key: ")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

class State(TypedDict):
    query: str
    category: str
    final_answer: str

def router_node(state: State) -> dict:
    
    prompt = f"Analyze the query and determine if it's about a 'joke' or 'math'. Query: {state['query']}. Return ONLY the word 'joke' or 'math'."
    response = llm.invoke(prompt)
    content = response.content[0].get("text", "") if isinstance(response.content, list) else response.content
    category = content.strip().lower() 
    return {"category" : category}

def joke_node(state: State) -> dict:
    prompt = f"Tell a joke based on the following topic: {state['query']}"
    response = llm.invoke(prompt)
    content = response.content[0].get("text", "") if isinstance(response.content, list) else response.content
    joke = content.strip()
    return {"final_answer": joke}

def math_node(state: State) -> dict:
    math = state["query"]
    prompt = f"Solve the following math problem step-by-step: {math}"
    response = llm.invoke(prompt)
    content = response.content[0].get("text", "") if isinstance(response.content, list) else response.content
    solution = content.strip()
    return {"final_answer": solution}

def route_category(state: State) -> str:
 
    if "joke" in state["category"]:
        return "joke"
    else:
        return "math"

builder = StateGraph(State)

builder.add_node("router", router_node)
builder.add_node("joke", joke_node)
builder.add_node("math", math_node)

builder.add_edge(START, "router")


builder.add_conditional_edges("router", route_category, {
    "joke": "joke",
    "math": "math"
})

builder.add_edge("joke", END)
builder.add_edge("math", END)

graph = builder.compile()

if __name__ == "__main__":
  
    print("Testing Math Query...")
    math_state = graph.invoke({"query": "What is 15 multiplied by 17?"})
    print("\nResult:", math_state.get("final_answer"))
    
    print("\n" + "="*40 + "\n")
    
    
    print("Testing Joke Query...")
    joke_state = graph.invoke({"query": "Tell me a joke about artificial intelligence"})
    print("\nResult:", joke_state.get("final_answer"))
