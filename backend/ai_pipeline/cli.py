import argparse
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, User, SessionLocal
from app.gmail import get_mailbox, FakeGmail
from ai_pipeline.pipeline import classify_new_threads
from ai_pipeline.agent import run_agent


def main():
    parser = argparse.ArgumentParser(description="Inbox Copilot AI Pipeline")
    subparsers = parser.add_subparsers(dest="command")
    
    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--mode", choices=["fake", "gmail"], default="fake")
    classify_parser.add_argument("--user", required=True, help="User email")
    classify_parser.add_argument("--limit", type=int, default=25)
    
    chat_parser = subparsers.add_parser("chat")
    chat_parser.add_argument("--mode", choices=["fake", "gmail"], default="fake")
    chat_parser.add_argument("--user", required=True, help="User email")
    chat_parser.add_argument("--message", help="Message to send (if not provided, enters interactive mode)")
    
    args = parser.parse_args()
    
    if args.command == "classify":
        if args.mode == "fake":
            db_url = "sqlite:///./fake_dev.db"
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            SessionLocal_temp = sessionmaker(bind=engine)
            db = SessionLocal_temp()
            mail = FakeGmail()
        else:
            db = SessionLocal()
            user = db.query(User).filter(User.email == args.user).first()
            if not user:
                print(f"User {args.user} not found")
                sys.exit(1)
            mail = get_mailbox(user)
            db.close()
            db = SessionLocal()
        
        user = db.query(User).filter(User.email == args.user).first()
        
        if not user:
            print(f"User {args.user} not found in database")
            sys.exit(1)
        
        try:
            classify_new_threads(db, user, mail, limit=args.limit)
            print(f"Classification complete for {args.user}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        finally:
            db.close()
    
    elif args.command == "chat":
        if args.mode == "fake":
            db_url = "sqlite:///./fake_dev.db"
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            SessionLocal_temp = sessionmaker(bind=engine)
            db = SessionLocal_temp()
            mail = FakeGmail()
        else:
            db = SessionLocal()
            user = db.query(User).filter(User.email == args.user).first()
            if not user:
                print(f"User {args.user} not found")
                sys.exit(1)
            mail = get_mailbox(user)
            db.close()
            db = SessionLocal()
        
        user = db.query(User).filter(User.email == args.user).first()
        if not user:
            print(f"User {args.user} not found in database")
            sys.exit(1)
        
        if args.message:
            answer, tool_calls = run_agent(db, user, mail, args.message)
            print(f"\nAnswer: {answer}")
            if tool_calls:
                print(f"Tools: {', '.join(tool_calls)}")
        else:
            print(f"Chat mode (user: {args.user}). Type 'exit' to quit.")
            while True:
                try:
                    msg = input("> ").strip()
                    if not msg or msg.lower() == "exit":
                        break
                    answer, tool_calls = run_agent(db, user, mail, msg)
                    print(f"\nAnswer: {answer}")
                    if tool_calls:
                        print(f"Tools: {', '.join(tool_calls)}")
                    print()
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error: {e}")
        
        db.close()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
