import pytest
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from app.db import Base, User, Thread, Draft
from app.main import create_app


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def test_user(test_db):
    user = User(id="user1", google_sub="sub1", email="nikhil@example.com")
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_thread(test_db, test_user):
    thread = Thread(
        id="thread1",
        user_id=test_user.id,
        gmail_thread_id="gthread1",
        subject="Test",
        sender="boss@company.com",
        status="new"
    )
    test_db.add(thread)
    test_db.commit()
    return thread


@pytest.fixture
def client(test_db):
    app = create_app()
    return TestClient(app)


class TestDraftAPI:
    def test_no_session_returns_401(self, client):
        response = client.post("/api/threads/t1/drafts", json={"instruction": "reply"})
        assert response.status_code == 401

    def test_list_no_session_returns_401(self, client):
        response = client.get("/api/threads/t1/drafts")
        assert response.status_code == 401

    def test_patch_no_session_returns_401(self, client):
        response = client.patch("/api/drafts/d1", json={"body": "new"})
        assert response.status_code == 401

    def test_discard_no_session_returns_401(self, client):
        response = client.post("/api/drafts/d1/discard")
        assert response.status_code == 401

    def test_create_draft_stores_row(self, test_db, test_user, test_thread):
        from unittest.mock import MagicMock, patch
        from ai_pipeline.schemas import DraftOut
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=test_user.id):
            with patch("app.routes.drafts.get_mailbox") as mock_get_mailbox:
                mock_mailbox = MagicMock()
                mock_mailbox.get_thread.return_value = {
                    "subject": "Test",
                    "messages": [
                        {
                            "sender": "boss@company.com",
                            "body": "Help",
                            "is_from_me": False,
                            "reply_to": "",
                            "list_unsubscribe": ""
                        }
                    ]
                }
                mock_get_mailbox.return_value = mock_mailbox
                
                with patch("app.routes.drafts.write_draft") as mock_write:
                    mock_write.return_value = DraftOut(
                        subject="Re: Test",
                        body="I can help",
                        needs_info=[]
                    )
                    
                    with patch("app.routes.drafts.flag_draft", return_value=[]):
                        with patch("app.routes.drafts.recipient_warning", return_value=None):
                            from starlette.testclient import TestClient
                            app = create_app()
                            client = TestClient(app)
                            
                            client.cookies.set("session", "fake_token")
                            response = client.post(
                                f"/api/threads/{test_thread.id}/drafts",
                                json={"instruction": "help me"}
                            )
                            
                            assert response.status_code == 200
                            data = response.json()
                            assert data["subject"] == "Re: Test"
                            assert data["body"] == "I can help"
                            
                            draft = test_db.query(Draft).filter_by(id=data["id"]).first()
                            assert draft is not None
                            assert draft.status == "draft"

    def test_patch_edits_body_while_draft(self, test_db, test_user):
        draft = Draft(
            id="d1",
            user_id=test_user.id,
            thread_id="t1",
            to_addr="boss@company.com",
            subject="Re: Test",
            body="Original body",
            status="draft"
        )
        test_db.add(draft)
        test_db.commit()
        
        from unittest.mock import patch
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=test_user.id):
            from starlette.testclient import TestClient
            app = create_app()
            client = TestClient(app)
            
            client.cookies.set("session", "fake_token")
            response = client.patch(
                "/api/drafts/d1",
                json={"body": "New body"}
            )
            
            assert response.status_code == 200
            updated_draft = test_db.query(Draft).filter_by(id="d1").first()
            assert updated_draft.body == "New body"

    def test_patch_refuses_after_discard(self, test_db, test_user):
        draft = Draft(
            id="d1",
            user_id=test_user.id,
            thread_id="t1",
            to_addr="boss@company.com",
            subject="Re: Test",
            body="Body",
            status="discarded"
        )
        test_db.add(draft)
        test_db.commit()
        
        from unittest.mock import patch
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=test_user.id):
            from starlette.testclient import TestClient
            app = create_app()
            client = TestClient(app)
            
            client.cookies.set("session", "fake_token")
            response = client.patch(
                "/api/drafts/d1",
                json={"body": "New"}
            )
            
            assert response.status_code == 409

    def test_discard_works_once(self, test_db, test_user):
        draft = Draft(
            id="d1",
            user_id=test_user.id,
            thread_id="t1",
            to_addr="boss@company.com",
            subject="Re: Test",
            body="Body",
            status="draft"
        )
        test_db.add(draft)
        test_db.commit()
        
        from unittest.mock import patch
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=test_user.id):
            from starlette.testclient import TestClient
            app = create_app()
            client = TestClient(app)
            
            client.cookies.set("session", "fake_token")
            
            response1 = client.post("/api/drafts/d1/discard")
            assert response1.status_code == 200
            
            response2 = client.post("/api/drafts/d1/discard")
            assert response2.status_code == 409

    def test_another_user_gets_404(self, test_db):
        user1 = User(id="user1", google_sub="sub1", email="user1@example.com")
        user2 = User(id="user2", google_sub="sub2", email="user2@example.com")
        test_db.add_all([user1, user2])
        
        thread = Thread(
            id="t1",
            user_id=user1.id,
            gmail_thread_id="g1",
            subject="Test",
            sender="sender@example.com",
            status="new"
        )
        test_db.add(thread)
        test_db.commit()
        
        from unittest.mock import patch
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=user2.id):
            from starlette.testclient import TestClient
            app = create_app()
            client = TestClient(app)
            
            client.cookies.set("session", "fake_token")
            response = client.get(f"/api/threads/t1/drafts")
            
            assert response.status_code == 404

    def test_list_returns_user_drafts(self, test_db, test_user):
        thread = Thread(
            id="t1",
            user_id=test_user.id,
            gmail_thread_id="g1",
            subject="Test",
            sender="sender@example.com",
            status="new"
        )
        test_db.add(thread)
        
        draft1 = Draft(
            id="d1",
            user_id=test_user.id,
            thread_id="t1",
            to_addr="sender@example.com",
            subject="Re: Test",
            body="Body1",
            status="draft"
        )
        draft2 = Draft(
            id="d2",
            user_id=test_user.id,
            thread_id="t1",
            to_addr="sender@example.com",
            subject="Re: Test 2",
            body="Body2",
            status="draft"
        )
        test_db.add_all([draft1, draft2])
        test_db.commit()
        
        from unittest.mock import patch
        
        with patch("app.routes.drafts._verify_session_cookie", return_value=test_user.id):
            from starlette.testclient import TestClient
            app = create_app()
            client = TestClient(app)
            
            client.cookies.set("session", "fake_token")
            response = client.get(f"/api/threads/t1/drafts")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
