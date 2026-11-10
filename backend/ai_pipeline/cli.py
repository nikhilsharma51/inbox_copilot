import argparse
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.db import Base, User, SessionLocal
from app.gmail import get_mailbox, FakeGmail
from ai_pipeline.pipeline import classify_new_threads


def main():
    parser = argparse.ArgumentParser(description="Inbox Copilot AI Pipeline")
    subparsers = parser.add_subparsers(dest="command")
    
    classify_parser = subparsers.add_parser("classify")
    classify_parser.add_argument("--mode", choices=["fake", "gmail"], default="fake")
    classify_parser.add_argument("--user", required=True, help="User email")
    classify_parser.add_argument("--limit", type=int, default=25)
    
    args = parser.parse_args()
    
    if args.command != "classify":
        parser.print_help()
        return
    
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


if __name__ == "__main__":
    main()
