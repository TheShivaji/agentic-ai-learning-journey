
from agents import Runner, SQLiteSession
from conversation_agent import conversation_agent, send_reply_email


async def run_agent_and_reply(
    sender_email: str,
    subject: str,
    body_text: str,
    session: SQLiteSession,
    in_reply_to_message_id: str | None,
):

    result = await Runner.run(
        conversation_agent,
        body_text,
        session=session,
    )
    reply_text = result.final_output


    reply_subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

    send_reply_email(
        to_address=sender_email,
        subject=reply_subject,
        text_body=reply_text,
        in_reply_to_message_id=in_reply_to_message_id,
    )
