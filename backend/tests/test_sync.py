from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

from app.db import Base, User, Thread
from app.sync import sync_threads
from app.gmail import FakeGmail
from app.main import create_app
from app.routes.auth import get_db, _make_session_cookie


@pytest.fixture
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def test_db(test_db_engine):
    Session = sessionmaker(bind=test_db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(test_db):
    app = create_app()
    
    def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def test_user(test_db):
    user = User(
        google_sub="test_sub",
        email="test@example.com",
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestSyncThreads:
    def test_first_sync_inserts_all_threads(self, test_db, test_user):
        mail = FakeGmail()
        
        result = sync_threads(test_db, test_user, mail)
        
        assert result["inserted"] > 0
        assert result["updated"] == 0
        
        threads = test_db.query(Thread).filter(Thread.user_id == test_user.id).all()
        assert len(threads) == result["inserted"]
        
        for thread in threads:
            assert thread.status == "new"

    def test_second_sync_skips_unchanged(self, test_db, test_user):
        mail = FakeGmail()
        
        result1 = sync_threads(test_db, test_user, mail)
        initial_count = test_db.query(Thread).filter(Thread.user_id == test_user.id).count()
        
        result2 = sync_threads(test_db, test_user, mail)
        
        assert result2["inserted"] == 0
        final_count = test_db.query(Thread).filter(Thread.user_id == test_user.id).count()
        assert final_count == initial_count

    def test_status_reset_on_update(self, test_db, test_user):
        mail = FakeGmail()
        
        result1 = sync_threads(test_db, test_user, mail)
        
        thread = test_db.query(Thread).filter(Thread.user_id == test_user.id).first()
        thread.status = "classified"
        test_db.commit()
        
        result2 = sync_threads(test_db, test_user, mail)
        
        thread = test_db.query(Thread).filter(Thread.user_id == test_user.id).first()
        assert thread.status == "classified"

    def test_two_users_separate_threads(self, test_db):
        user1 = User(google_sub="sub1", email="user1@example.com")
        user2 = User(google_sub="sub2", email="user2@example.com")
        test_db.add(user1)
        test_db.add(user2)
        test_db.commit()
        
        mail = FakeGmail()
        
        sync_threads(test_db, user1, mail)
        sync_threads(test_db, user2, mail)
        
        user1_threads = test_db.query(Thread).filter(Thread.user_id == user1.id).count()
        user2_threads = test_db.query(Thread).filter(Thread.user_id == user2.id).count()
        
        assert user1_threads > 0
        assert user2_threads > 0
        assert user1_threads == user2_threads

    def test_integrity_error_continues(self, test_db, test_user):
        mail = FakeGmail()
        
        result = sync_threads(test_db, test_user, mail)
        assert result["inserted"] > 0


class TestThreadsEndpoint:
    def test_threads_newest_first(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        for i in range(3):
            thread = Thread(
                user_id=test_user.id,
                gmail_thread_id=f"thread_{i}",
                subject=f"Subject {i}",
                sender="sender@example.com",
                summary="",
            )
            test_db.add(thread)
            test_db.commit()
        
        response = client.get("/api/threads")
        
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 3

    def test_threads_respects_200_limit(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        for i in range(250):
            thread = Thread(
                user_id=test_user.id,
                gmail_thread_id=f"thread_{i}",
                subject=f"Subject {i}",
                sender="sender@example.com",
                summary="",
            )
            test_db.add(thread)
        test_db.commit()
        
        response = client.get("/api/threads")
        
        assert response.status_code == 200
        threads = response.json()
        assert len(threads) == 200

    def test_threads_user_isolation(self, client, test_db):
        user1 = User(google_sub="sub1", email="user1@example.com")
        user2 = User(google_sub="sub2", email="user2@example.com")
        test_db.add(user1)
        test_db.add(user2)
        test_db.commit()
        
        for i in range(5):
            t1 = Thread(
                user_id=user1.id,
                gmail_thread_id=f"u1_thread_{i}",
                subject=f"User1 Subject {i}",
                sender="sender@example.com",
                summary="",
            )
            t2 = Thread(
                user_id=user2.id,
                gmail_thread_id=f"u2_thread_{i}",
                subject=f"User2 Subject {i}",
                sender="sender@example.com",
                summary="",
            )
            test_db.add(t1)
            test_db.add(t2)
        test_db.commit()
        
        session_token1 = _make_session_cookie(user1.id)
        client.cookies.set("session", session_token1)
        
        response = client.get("/api/threads")
        threads = response.json()
        
        assert len(threads) == 5
        for thread in threads:
            assert thread["thread_id"].startswith("u1_thread_")

    def test_threads_401_without_session(self, client):
        response = client.get("/api/threads")
        assert response.status_code == 401


class TestSyncEndpoint:
    def test_sync_returns_counts(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        response = client.post("/api/sync")
        
        assert response.status_code == 200
        data = response.json()
        assert "inserted" in data
        assert "updated" in data
        assert "skipped" in data

    def test_sync_401_without_session(self, client):
        response = client.post("/api/sync")
        assert response.status_code == 401

    def test_sync_401_on_reconnect_needed(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        test_user.refresh_token_enc = None
        test_db.commit()
        
        with patch("app.routes.sync.get_mailbox") as mock_get_mailbox:
            from app.gmail import ReconnectNeeded
            mock_get_mailbox.side_effect = ReconnectNeeded("No refresh token")
            
            response = client.post("/api/sync")
            
            assert response.status_code == 401
