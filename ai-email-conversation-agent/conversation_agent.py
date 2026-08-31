
import os
from agents import Agent, set_default_openai_api
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Header, ReplyTo

set_default_openai_api("chat_completions")

from sales_agent import MODEL_NAME

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

AI_EMAIL_ADDRESS = os.getenv("AI_EMAIL_ADDRESS", "ai@parse.theshivaji.in")
INBOUND_EMAIL_ADDRESS = os.getenv("INBOUND_EMAIL_ADDRESS", "ai@parse.theshivaji.in")

if SENDGRID_API_KEY:
    print(f"SendGrid API Key exists and begins {SENDGRID_API_KEY[:8]}")
else:
    print("SENDGRID_API_KEY not set - reply emails will fail")

conversation_instructions = """
You are a helpful AI assistant that responds to users over email.

The user has emailed you a question or message. You have access to the
full previous conversation history with this specific user (if any).

Guidelines:
- Answer clearly and directly.
- If the user refers to something from earlier in the conversation
  (like "why do we need that" or "explain more"), use the conversation
  history to understand what they mean.
- Keep your tone friendly and professional, like a helpful email reply.
- Do not repeat the entire previous conversation back to the user -
  just respond naturally, like a human continuing an email thread.
"""

conversation_agent = Agent(
    name="Email Conversation Agent",
    instructions=conversation_instructions,
    model=MODEL_NAME,   # <- same string-based pattern jo tumne already use kiya hai
)

def send_reply_email(
    to_address: str,
    subject: str,
    text_body: str,
    in_reply_to_message_id: str | None = None,
) -> None:
    

    message = Mail(
        from_email=AI_EMAIL_ADDRESS,
        to_emails=to_address,
        subject=subject,
        plain_text_content=text_body,
    )
    

    message.reply_to = ReplyTo(INBOUND_EMAIL_ADDRESS)

    if in_reply_to_message_id:
        message.add_header(Header("In-Reply-To", in_reply_to_message_id))
        message.add_header(Header("References", in_reply_to_message_id))

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    
    try:
        from python_http_client.exceptions import HTTPError
        response = sg.send(message)
    except HTTPError as e:
        print(f"SENDGRID ERROR BODY: {e.body}")
        raise

    if response.status_code >= 300:
        raise RuntimeError(
            f"SendGrid reply send failed: {response.status_code} - {response.body}"
        )
