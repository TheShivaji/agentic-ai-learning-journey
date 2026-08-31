import re
import hashlib


def _extract_first_reference(references_header: str) -> str | None:
    """
    References header me multiple Message-IDs hote hain, space se
    separated, angle brackets ke andar. Example:

        "<msg1@mail.com> <msg2@mail.com> <msg3@mail.com>"

    Hum PEHLA nikaalte hain kyunki wahi thread ka root hai.
    """
    if not references_header:
        return None
    matches = re.findall(r"<[^>]+>", references_header)
    return matches[0] if matches else None


def _normalize_subject(subject: str) -> str:
    """
    "Re: Re: Fwd: What is RAG?" -> "what is rag?"
    Taaki same conversation ke saare subject-variants match karein.
    """
    if not subject:
        return ""
    cleaned = re.sub(r"(?i)^(re|fwd|fw)\s*:\s*", "", subject.strip())
    # kabhi kabhi "Re: Fwd: Re:" multiple prefixes hote hain, isliye loop
    prev = None
    while prev != cleaned:
        prev = cleaned
        cleaned = re.sub(r"(?i)^(re|fwd|fw)\s*:\s*", "", cleaned.strip())
    return cleaned.strip().lower()


def get_session_id(
    sender_email: str,
    subject: str,
    message_id: str | None = None,
    in_reply_to: str | None = None,
    references: str | None = None,
) -> str:
    """
    Ye function hi asli "thread ID -> session ID" mapping karta hai.
    Isse webhook.py call karega har inbound email ke liye.

    Returns: ek stable, filesystem/db-safe string jo SQLiteSession ka
             session_id banega.
    """

    root_id = _extract_first_reference(references)

    if not root_id and in_reply_to:
        root_id = in_reply_to.strip()

    if root_id:
        raw_key = f"thread:{root_id}"
    else:
        normalized_subject = _normalize_subject(subject)
        raw_key = f"new:{sender_email.lower().strip()}:{normalized_subject}"

    session_id = hashlib.sha256(raw_key.encode()).hexdigest()[:24]
    return session_id


if __name__ == "__main__":
    # Case 1: User A ka pehla email (koi headers nahi)
    s1 = get_session_id(
        sender_email="usera@gmail.com",
        subject="What is RAG?",
    )
    print("First email session:", s1)

    # Case 2: User A ka reply (In-Reply-To set hoga, References bhi)
    s2 = get_session_id(
        sender_email="usera@gmail.com",
        subject="Re: What is RAG?",
        in_reply_to="<original-msg-id@gmail.com>",
        references="<original-msg-id@gmail.com>",
    )
    print("Reply session (should match s1's thread root logic):", s2)

    # Case 3: User B ka alag email -> alag session
    s3 = get_session_id(
        sender_email="userb@gmail.com",
        subject="What is RAG?",
    )
    print("User B session (different from A):", s3)

    assert s1 != s3, "Different users should get different sessions!"
    
