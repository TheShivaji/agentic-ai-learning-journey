import re
import email.utils
from fastapi import FastAPI, Form, Request

from thread_mapper import get_session_id
from session_store import get_session
from agent_runner import run_agent_and_reply   # tumhara integration point

app = FastAPI()


def _extract_header(raw_headers: str, header_name: str) -> str | None:
    """
    SendGrid 'headers' field me PURA raw email header block string
    ke roop me aata hai, jaise:

        "Received: from ...\\nMessage-ID: <abc@mail.com>\\n
         In-Reply-To: <xyz@mail.com>\\nSubject: ...\\n..."

    Hume isme se specific header (Message-ID / In-Reply-To / References)
    dhoondhna padta hai, kyunki SendGrid inhe alag se structured field
    me nahi deta.
    """
    if not raw_headers:
        return None
    pattern = rf"^{header_name}:\s*(.+)$"
    match = re.search(pattern, raw_headers, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_sender_email(from_field: str) -> str:
    """
    "John Doe <john@example.com>"  ->  "john@example.com"
    email.utils.parseaddr yahi karta hai, standard library hai,
    khud regex likhne ki zaroorat nahi.
    """
    name, addr = email.utils.parseaddr(from_field)
    return addr


@app.post("/webhook/inbound-email")
async def inbound_email(request: Request):
    """
    SendGrid isi URL pe POST karega. Hum Request.form() se saara
    multipart data nikaalte hain (Form(...) individual params ki jagah
    Request.form() isliye use kiya kyunki SendGrid kabhi kabhi extra
    fields bhejta hai jo humein predict nahi karni - flexible rehta hai).
    """
    form = await request.form()

    sender_raw = form.get("from", "")
    subject = form.get("subject", "(no subject)")
    body_text = form.get("text", "") or form.get("html", "")
    raw_headers = form.get("headers", "")

    sender_email = _extract_sender_email(sender_raw)
    message_id = _extract_header(raw_headers, "Message-ID")
    in_reply_to = _extract_header(raw_headers, "In-Reply-To")
    references = _extract_header(raw_headers, "References")


    session_id = get_session_id(
        sender_email=sender_email,
        subject=subject,
        message_id=message_id,
        in_reply_to=in_reply_to,
        references=references,
    )


    session = get_session(session_id)


    await run_agent_and_reply(
        sender_email=sender_email,
        subject=subject,
        body_text=body_text,
        session=session,
        in_reply_to_message_id=message_id,
    )


    return {"status": "received"}
