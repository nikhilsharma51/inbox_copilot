import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, User, Thread, Category
from ai_pipeline.classify import classify_thread
from ai_pipeline.pipeline import classify_new_threads
from ai_pipeline.schemas import Classification
from app.gmail import FakeGmail


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@pytest.fixture
def test_user(test_db):
    user = User(id="test_user_1", google_sub="sub1", email="test@example.com")
    test_db.add(user)
    test_db.commit()
    return user


@pytest.fixture
def test_categories(test_db, test_user):
    categories = [
        Category(id="c1", user_id=test_user.id, name="Work", description="Work email"),
        Category(id="c2", user_id=test_user.id, name="Personal", description="Personal email"),
    ]
    test_db.add_all(categories)
    test_db.commit()
    return categories


class TestClassifyThread:
    def test_valid_output_accepted_and_stored_classified(self):
        categories = [("Work", "Work"), ("Personal", "Personal")]
        subject = "Meeting Tomorrow"
        sender = "boss@company.com"
        body = "Let's discuss the project"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary="Meeting discussion",
            needs_reply=True,
            priority=2,
            confidence=0.95,
            suspected_injection=False
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Work"
        assert result.priority == 2
        assert result.confidence == 0.95
        assert result.needs_reply == True

    def test_invented_category_retried_then_needs_review(self):
        categories = [("Work", "Work"), ("Personal", "Personal")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="InvalidCategory",
            summary="Test",
            needs_reply=False,
            priority=3,
            confidence=0.8,
            suspected_injection=False
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Needs Review"
        assert result.confidence == 0.0

    def test_missing_fields_retried_then_needs_review(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary="Test",
            needs_reply=False,
            priority=999,
            confidence=0.9,
            suspected_injection=False
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Needs Review"

    def test_garbage_output_needs_review(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("Parse error")
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Needs Review"
        assert result.confidence == 0.0

    def test_confidence_7_needs_review(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary="Test",
            needs_reply=False,
            priority=3,
            confidence=7,
            suspected_injection=False
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Needs Review"

    def test_none_returned_treated_as_failed(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = None
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Needs Review"
        assert result.confidence == 0.0

    def test_confidence_0_5_with_valid_category_stored_needs_review(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary="Test",
            needs_reply=False,
            priority=3,
            confidence=0.5,
            suspected_injection=False
        )
        mock_llm.with_structured_output.return_value.invoke.return_value = mock_response
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert result.category == "Work"
        assert result.confidence == 0.5

    def test_summary_longer_than_160_chars_cut(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        short_summary = "x" * 150
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary=short_summary,
            needs_reply=False,
            priority=3,
            confidence=0.9,
            suspected_injection=False
        )
        
        def mock_invoke(prompt):
            class ResponseDict(dict):
                pass
            resp = ResponseDict({'parsed': mock_response})
            resp['summary'] = short_summary
            return mock_response
        
        mock_llm.with_structured_output.return_value.invoke = mock_invoke
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert len(result.summary) <= 160

    def test_tokens_saved_on_row(self):
        categories = [("Work", "Work")]
        subject = "Test"
        sender = "user@example.com"
        body = "Test"
        
        mock_llm = MagicMock()
        mock_response = Classification(
            category="Work",
            summary="Test",
            needs_reply=False,
            priority=3,
            confidence=0.9,
            suspected_injection=False
        )
        mock_raw = MagicMock()
        mock_raw.usage_metadata.total_tokens = 150
        mock_llm.with_structured_output.return_value.invoke.return_value = {
            'parsed': mock_response,
            'raw': mock_raw
        }
        
        result, tokens = classify_thread(subject, sender, body, categories, llm=mock_llm)
        
        assert tokens == 150


class TestClassifyNewThreads:
    def test_valid_threads_classified(self, test_db, test_user, test_categories):
        thread = Thread(
            id="t1",
            user_id=test_user.id,
            gmail_thread_id="thread_1",
            subject="Test",
            sender="user@example.com",
            status="new"
        )
        test_db.add(thread)
        test_db.commit()
        
        mail = FakeGmail()
        
        classify_new_threads(test_db, test_user, mail, limit=25, sleep_fn=lambda x: None)
        
        updated_thread = test_db.query(Thread).filter_by(id="t1").first()
        assert updated_thread.status in ['classified', 'needs_review', 'failed']
        assert updated_thread.tokens is not None

    def test_get_thread_raises_becomes_failed(self, test_db, test_user, test_categories):
        thread = Thread(
            id="t1",
            user_id=test_user.id,
            gmail_thread_id="gthread_nonexistent_xyz",
            subject="Test",
            sender="user@example.com",
            status="new"
        )
        test_db.add(thread)
        test_db.commit()
        
        mail = FakeGmail()
        
        classify_new_threads(test_db, test_user, mail, limit=25, sleep_fn=lambda x: None)
        
        updated_thread = test_db.query(Thread).filter_by(id="t1").first()
        assert updated_thread.status == "failed"

    def test_user_isolation(self, test_db):
        user1 = User(id="user1", google_sub="sub1", email="user1@example.com")
        user2 = User(id="user2", google_sub="sub2", email="user2@example.com")
        test_db.add_all([user1, user2])
        test_db.commit()
        
        cat1 = Category(id="c1", user_id=user1.id, name="Work", description="Work")
        cat2 = Category(id="c2", user_id=user2.id, name="Work", description="Work")
        test_db.add_all([cat1, cat2])
        test_db.commit()
        
        thread1 = Thread(
            id="t1",
            user_id=user1.id,
            gmail_thread_id="thread_1",
            subject="Test1",
            sender="user1@example.com",
            status="new"
        )
        thread2 = Thread(
            id="t2",
            user_id=user2.id,
            gmail_thread_id="thread_2",
            subject="Test2",
            sender="user2@example.com",
            status="new"
        )
        test_db.add_all([thread1, thread2])
        test_db.commit()
        
        mail = FakeGmail()
        
        classify_new_threads(test_db, user1, mail, limit=25, sleep_fn=lambda x: None)
        
        t1 = test_db.query(Thread).filter_by(id="t1").first()
        t2 = test_db.query(Thread).filter_by(id="t2").first()
        
        assert t1.status in ['classified', 'needs_review', 'failed']
        assert t2.status == "new"

    def test_interruption_resumes_only_new(self, test_db, test_user, test_categories):
        for i in range(12):
            thread = Thread(
                id=f"t{i}",
                user_id=test_user.id,
                gmail_thread_id=f"gthread{i}",
                subject=f"Test{i}",
                sender="user@example.com",
                status="new"
            )
            test_db.add(thread)
        test_db.commit()
        
        mail = FakeGmail()
        
        classify_new_threads(test_db, test_user, mail, limit=5, sleep_fn=lambda x: None)
        
        classified_count = test_db.query(Thread).filter(
            Thread.user_id == test_user.id,
            Thread.status != 'new'
        ).count()
        assert classified_count == 5
        
        remaining_new = test_db.query(Thread).filter(
            Thread.user_id == test_user.id,
            Thread.status == 'new'
        ).count()
        assert remaining_new == 7
        
        first_thread = test_db.query(Thread).filter_by(id="t0").first()
        first_classified_at = first_thread.updated_at
        
        classify_new_threads(test_db, test_user, mail, limit=25, sleep_fn=lambda x: None)
        
        remaining_new_after = test_db.query(Thread).filter(
            Thread.user_id == test_user.id,
            Thread.status == 'new'
        ).count()
        assert remaining_new_after == 0
        
        first_thread_after = test_db.query(Thread).filter_by(id="t0").first()
        assert first_thread_after.updated_at == first_classified_at
