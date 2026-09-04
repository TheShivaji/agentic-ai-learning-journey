# Imports and environment first, as always

import os
import getpass
from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from IPython.display import Image, display
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

class State(TypedDict):
    messages: Annotated[list, add_messages]
    spanish: str
    hindi:str
    sentiment:str
    report:str

# Ek tool ka code
search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())
tools = [search]
llm_with_tools = llm.bind_tools(tools)

def chatbot_node(state: State) -> dict:
    print("\n👉 [NODE: Chatbot] ke andar aa gaye.")
    print(f"📝 Current Memory (State) mein messages: {len(state['messages'])}")
    
    # LLM ko call karna
    response = llm_with_tools.invoke(state["messages"])
    
    print(f"🤖 LLM ka Reply: {response.content if response.content else 'Koi Tool Call kiya hai'}")
    print("✅ [NODE: Chatbot] se nikal rahe hain.\n")
    return {"messages": [response]}

def translator_node(state: State) -> dict:
    last = state["messages"][-1].content
    print ("translator_node")
    prompt = f"Translate this into Spanish, replying with the translation only:\n\n{last}"
    return {"spanish": llm.invoke(prompt).content}

def hindi_node(state : State) -> dict:
    last = state["messages"][-1].content
    prompt = f"Translate this message into Hindi, replying with the translation only:\n\n{last}"
    return {"hindi": llm.invoke(prompt).content}

def mood_node(state : State) -> dict:
    last = state["messages"][-1].content
    prompt = f"Analyze the sentiment of the user's message and reply with the result only:\n\n{last}"
    return {"sentiment": llm.invoke(prompt).content}

def report_node(state : State) -> dict:
    spanish = state["spanish"]
    hindi = state["hindi"]
    sentiment = state["sentiment"]
    report = f"Spanish: {spanish}\nHindi: {hindi}\nSentiment: {sentiment}"
    return {"report": report}

memory = MemorySaver()

# Final graph definition
builder = StateGraph(State)
builder.add_node("chatbot", chatbot_node)
builder.add_node("tools", ToolNode(tools))
builder.add_node("translator", translator_node)
builder.add_node("hindi", hindi_node)
builder.add_node("mood", mood_node)
builder.add_node("report", report_node)

builder.add_edge(START, "chatbot")
builder.add_conditional_edges("chatbot", tools_condition, {"tools": "tools", END: "translator"})
builder.add_edge("translator", "hindi")
builder.add_edge("hindi", "mood")
builder.add_edge("mood", "report")
builder.add_edge("report", END)
builder.add_edge("tools", "chatbot")

graph = builder.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "conversation-1"}}
graph.invoke({"messages": [{"role": "user", "content": "Hi, my name is Ed."}]}, config)
second = graph.invoke({"messages": [{"role": "user", "content": "What is my name?"}]}, config)

print(second["messages"][-1].content)
print(second["spanish"])