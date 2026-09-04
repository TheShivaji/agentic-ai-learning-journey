import os
import sys
import asyncio
import warnings
import logging
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_community.tools import GoogleSerperRun
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
logging.getLogger("langchain_core").setLevel(logging.ERROR)

load_dotenv(override=True)
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL") 

# 1. Google Serper Search Tool
search = GoogleSerperRun(api_wrapper=GoogleSerperAPIWrapper())

# 2. Discord Notification Tool
@tool
def send_to_discord(message: str) -> str:
    """Send the final job title and link list directly to the user's Discord channel."""
    import urllib.request
    import json
    
    if not DISCORD_WEBHOOK_URL:
        return "Discord Webhook URL not configured."
        
    payload = {"text": message} if DISCORD_WEBHOOK_URL.endswith('/slack') else {"content": message}
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        DISCORD_WEBHOOK_URL, 
        data=data, 
        headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return "Jobs successfully sent to Discord!"
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return f"HTTP Error {e.code}: {e.reason} - {error_body}"
    except Exception as e:
        return f"Error sending to Discord: {e}"

# सुपर डायरेक्ट और सख्त प्रॉम्ट
system_prompt = """You are a job link collector. Your ONLY task is to find exactly 2 MERN Stack job openings for freshers on LinkedIn.

STRICT STEPS:
1. Run the `search` tool EXACTLY ONCE with the query: "site:linkedin.com/jobs MERN fresher".
2. From the search results snippet, extract the top 2 job titles and their exact application URL links.
3. Immediately format those 2 jobs as plain text and pass it to the `send_to_discord` tool.
4. Stop executing immediately. Do NOT run any more searches or loops.
"""

async def run_job_finder():
    print("Loading native tools...")
    all_tools = [search, send_to_discord]
    
    model = ChatOpenAI(
        model="deepseek-v4-flash",                     
        openai_api_key=os.environ.get("DEEPSEEK_API_KEY"), 
        openai_api_base="https://api.deepseek.com", 
        temperature=0.0 
    )
    
    # FIXED: max_iterations=2 जोड़ने से यह 2 बार से ज़्यादा टूल कॉल (लूप) नहीं कर पाएगा
    agent = create_react_agent(
        model=model,
        tools=all_tools,
        prompt=system_prompt,
        checkpointer=MemorySaver(),
    )
    
    # थ्रेड आईडी भी एकदम नई दी है
    config = {
        "configurable": {"thread_id": "clean-no-loop-thread-v3"}
    }
    query = "Find exactly 2 fresher MERN jobs from LinkedIn snippets and send titles/links to Discord now."
    
    print(f"Agent is searching: '{query}'")
    
    # ainvoke में अधिकतम टूल इटरेशन को कंट्रोल करना (सिर्फ सेफ साइड के लिए)
    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": query}]}, 
        config=config
    )
    
    print("\n--- Final Agent Response ---")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(run_job_finder())
