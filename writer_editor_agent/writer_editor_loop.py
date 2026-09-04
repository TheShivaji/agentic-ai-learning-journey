import os
import getpass
from typing_extensions import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(override=True)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")

llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")

class State(TypedDict):
    topic: str
    draft: str
    feedback: str
    is_approved: bool
    iteration_count: int

def writer_node(state: State) -> dict:
    print(f"\n✍️ [WRITER NODE] Iteration: {state.get('iteration_count', 0)}")
    topic = state["topic"]
    feedback = state.get("feedback", "")
    
    if feedback == "":
        prompt = f"Write a short, engaging 2-sentence paragraph about '{topic}'."
    else:
        print(f"   (Revising based on Editor's feedback: {feedback})")
        prompt = f"Rewrite this paragraph about '{topic}' based on the editor's feedback.\nFeedback: {feedback}\nDraft: {state['draft']}"
        
    response = llm.invoke(prompt)
    new_draft = response.content.strip()
    current_count = state.get("iteration_count", 0)
    return {"draft": new_draft, "iteration_count": current_count + 1}

def editor_node(state: State) -> dict:
    print("\n🧐 [EDITOR NODE] Checking draft...")
    draft = state["draft"]
    
    prompt = f"""
    Review this draft about '{state['topic']}'. 
    If it is interesting and well-written, reply ONLY with the word 'APPROVE'. 
    If it needs work, reply with 'REJECT: <reason why it needs work>'. 
    
    Draft: {draft}
    """
    
    response = llm.invoke(prompt)
    content = response.content.strip()
    
    if "APPROVE" in content.upper():
        print("   ✅ Editor Approved!")
        return {"is_approved": True, "feedback": ""}
    else:
        reason = content.replace("REJECT:", "").strip()
        print(f"   ❌ Editor Rejected. Reason: {reason}")
        return {"is_approved": False, "feedback": reason}

def should_continue(state: State) -> str:
    if state.get("iteration_count", 0) >= 3:
        print("\n⚠️ Max iterations reached (3 attempts)! Forcing graph to END.")
        return END
        
    if state.get("is_approved", False):
        return END
        
    print("\n🔄 Editor not happy. Routing back to Writer for revision...")
    return "writer"

builder = StateGraph(State)
builder.add_node("writer", writer_node)
builder.add_node("editor", editor_node)

builder.add_edge(START, "writer")
builder.add_edge("writer", "editor")

builder.add_conditional_edges(
    "editor",
    should_continue,
    {
        "writer": "writer",
        END: END
    }
)

graph = builder.compile()

if __name__ == "__main__":
    initial_state = {
        "topic": "Why cats are secret agents",
        "draft": "",
        "feedback": "",
        "is_approved": False,
        "iteration_count": 0
    }

    final_state = graph.invoke(initial_state)
    print("\n🎉 FINAL APPROVED DRAFT 🎉")
    print(final_state["draft"])
