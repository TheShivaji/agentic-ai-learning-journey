
from agents import SQLiteSession


DB_PATH = "email_conversations.db"


def get_session(session_id: str) -> SQLiteSession:
    """
    Har inbound email process karne se pehle isko call karo.
    Same session_id doge to purani history mil jaayegi, naya session_id
    doge to fresh conversation start hogi.
    """
    return SQLiteSession(session_id=session_id, db_path=DB_PATH)


# developer only don't useful for user
async def print_history(session_id: str):
    session = get_session(session_id)
    items = await session.get_items()
    for item in items:
        print(item)
