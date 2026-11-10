import sys
import uuid

from app.db import engine, SessionLocal, Base, User, Category


def reset_db(user_email: str):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    session = SessionLocal()

    user = User(
        id=str(uuid.uuid4()),
        google_sub=f"sub_{user_email}",
        email=user_email,
    )
    session.add(user)
    session.commit()

    default_categories = [
        Category(user_id=user.id, name="Follow-up", description="Needs a reply"),
        Category(user_id=user.id, name="FYI", description="For information only"),
        Category(user_id=user.id, name="Action", description="Requires action"),
    ]
    session.add_all(default_categories)
    session.commit()

    session.close()
    print(f"Database reset. Created user: {user_email}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/reset_db.py <user_email>")
        sys.exit(1)

    user_email = sys.argv[1]
    reset_db(user_email)
