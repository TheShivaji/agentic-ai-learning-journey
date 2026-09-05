from sidekick_tools import get_all_tools
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from dotenv import load_dotenv
from langchain.agents.middleware import (
    TodoListMiddleware,
    
    ModelCallLimitMiddleware,
    HumanInTheLoopMiddleware,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
import uuid



class EvaluatorOutput(BaseModel):
    success: bool = Field(description="True if success criteria met")
    feedback: str = Field(description="Feedback for the worker")
    needs_clarification : bool = Field(description="True if assistant needs clarification from user")

WORKER_PROMPT = """You are a shopping assistant. Help users find and purchase products.

* Use the search tool to find products.
* Use the purchase tool only when the user clearly wants to buy.
* Never make up product or order information.
* Ask for clarification if needed.
"""
MAX_ATTEMPTS = 3
load_dotenv(override=True)

class sidekickAgent:
    def __init__(self):
            self.session_id = str(uuid.uuid4())
            self.tool = []
            self.worker = None
            self.evaluator = None
            self.success_criteria = ""
            self.todos = []
            self.attempts = 0
            self.pending_actions = None
            self.paused = False
            self.task = ""
            self.history = []
            




    async def setup(self):
            self.tool = await get_all_tools()
            self.worker = create_agent(
                model="google_genai:gemini-3.5-flash-lite",
                system_prompt=WORKER_PROMPT,
                tools=self.tool,
                middleware=[
                    ModelCallLimitMiddleware(run_limit = 10 ),
                    HumanInTheLoopMiddleware(interrupt_on = {"buy_product" : {"instructions" : "Human needs to approve before buying"}}),
                    TodoListMiddleware()
                ],
                checkpointer=InMemorySaver()
            )
            self.evaluator = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite").with_structured_output(EvaluatorOutput)

    async def run(self , message : str):
        return await self.worker.ainvoke({"messages" : [{"role" : "user" , "content" : message}]})

    async def evaluate(self,message : str , success_criteria : str , last_reply : str , tools_used : list[str]) -> EvaluatorOutput:
        prompt = f"""You decide whether an assistant has met the success criteria for a task.

The user's request was:
{message}

The success criteria are:
{success_criteria}

The tools the assistant called while working, in order:
{', '.join(tools_used) or 'none'}

The assistant's most recent reply was:
{last_reply}

Decide whether the success criteria are met, using the tool calls as evidence of what was actually done.
Also decide whether the assistant needs more input from the user, either because it asked a question,
needs clarification, or seems stuck. Give brief, concrete feedback."""
        return await self.evaluator.ainvoke(prompt)

    async def run_turn(self , message : str , success_criteria  : str , last_reply : str , tools_used : list[str] , history: list) -> list[str]:
        self.task = message
        self.success_critera = success_critera
        self.attempts = 0
        self.todos = []
        payload = {
             "messages": [
                 {
                     "role": "user",
                     "content": f"{message}\n\nThe success criteria for this task are: {self.success_criteria}",
                 }
            ]
        }
        return await self._advance(payload, history + [{"role": "user", "content": message}])
        
    async def resume(self, history: list) -> list:
        """Approve the actions the worker paused on, and continue the turn."""
        payload = Command(resume={"decisions": [{"type": "approve"}] * self.pending_actions})
        return await self._advance(payload, history)

    async def _advance(self , history : list , payload: any) -> list[str]:
        config = {"configurable" : {"thread_id" : self.session_id}}
        while True:
            result = None

            async for result in self.worker.astream(payload, config=config, stream_mode="values"):
                self.todos = result.get("todos" , self.todos)

                if "__interrupt__" in result:
                    actions = result["__interrupt__"][0].value["action_requests"]
                    self.paused = True
                    self.pending_actions = len(actions)
                    described = "\n".join(action["description"] for action in actions)
                    return history + [{"role": "assistant", "content": f"Waiting for your approval:\n{described}"}]

            self.paused = False
            reply = result["messages"][-1].content
            tools_used = [
                call["name"] for m in result["messages"] for call in (getattr(m, "tool_calls", None) or [])
            ]
            self.attempts += 1
            verdict = await self.evaluate(self.task, self.success_criteria, reply, tools_used)
            if verdict.success or verdict.needs_clarification or self.attempts >= MAX_ATTEMPTS:
                return history + [
                        {"role": "assistant", "content": reply},
                        {"role": "assistant", "content": f"Evaluator: {verdict.feedback}"},
                ]
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Your last response did not meet the success criteria. "
                        f"Here is the feedback: {verdict.feedback}. Please keep working and address it.",
                    }
                ]
            }

                  
                    
                    
            
            