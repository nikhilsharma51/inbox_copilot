import sys
from sqlalchemy.orm import Session

from app.db import SessionLocal, User
from app.gmail import GmailClient, get_valid_access_token, ReconnectNeeded


def print_subjects(user_email: str):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User {user_email} not found")
            return
        
        try:
            access_token = get_valid_access_token(user)
        except ReconnectNeeded as e:
            print(f"Need to reconnect: {e}")
            return
        
        client = GmailClient(access_token=access_token)
        threads = client.list_threads(max_results=10)
        
        print(f"Subjects from {user_email}:")
        for i, thread in enumerate(threads, 1):
            print(f"{i}. {thread['subject']}")
    
    finally:
        session.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/print_subjects.py <user_email>")
        sys.exit(1)
    
    user_email = sys.argv[1]
    print_subjects(user_email)
