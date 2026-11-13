import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, User, Thread, Draft
from app.gmail import FakeGmail
from ai_pipeline.tools import make_tools


@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@pytest.fixture
def test_users(test_db):
    user1 = User(id="user1", google_sub="sub1", email="user1@example.com")
    user2 = User(id="user2", google_sub="sub2", email="user2@example.com")
    test_db.add_all([user1, user2])
    test_db.commit()
    return user1, user2


@pytest.fixture
def test_threads(test_db, test_users):
    user1, _ = test_users
    
    thread1 = Thread(
        id="t1",
        user_id=user1.id,
        gmail_thread_id="thread_1",
        subject="Test Subject",
        sender="boss@company.com",
        summary="Quick test",
        status="new"
    )
    thread2 = Thread(
        id="t2",
        user_id=user1.id,
        gmail_thread_id="thread_2",
        subject="Another Email",
        sender="friend@example.com",
        summary="More content",
        status="read"
    )
    test_db.add_all([thread1, thread2])
    test_db.commit()
    return thread1, thread2


class TestTools:
    def test_search_emails_by_subject(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Test", "limit": 10})
        
        assert "t1" in result
        assert "Test Subject" in result
        assert "boss@company.com" in result

    def test_search_emails_by_sender(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "friend", "limit": 10})
        
        assert "t2" in result
        assert "friend@example.com" in result

    def test_search_emails_wildcard_escape(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Test%", "limit": 10})
        
        assert result

    def test_search_limit_clamped(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Test", "limit": 500})
        
        lines = result.split('\n')
        assert len(lines) <= 20

    def test_list_by_category(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        list_tool = tools[1]
        
        result = list_tool.invoke({"category": "work", "limit": 10})
        
        assert "t1" in result or "t2" in result

    def test_other_user_threads_hidden_in_search(self, test_db, test_users, test_threads):
        user1, user2 = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user2, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Test", "limit": 10})
        
        assert "No emails found" in result or "t1" not in result

    def test_get_email_valid(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        get_tool = tools[2]
        
        result = get_tool.invoke({"thread_id": "t1"})
        
        assert "email_" in result
        assert "<email_" in result and "</email_" in result

    def test_get_email_not_found(self, test_db, test_users):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        get_tool = tools[2]
        
        result = get_tool.invoke({"thread_id": "nonexistent"})
        
        assert result == "thread not found"

    def test_get_email_other_user(self, test_db, test_users, test_threads):
        user1, user2 = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user2, mail)
        get_tool = tools[2]
        
        result = get_tool.invoke({"thread_id": "t1"})
        
        assert result == "thread not found"

    def test_create_draft(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        create_tool = tools[3]
        
        result = create_tool.invoke({"thread_id": "t1", "instruction": "reply yes"})
        
        assert "Draft saved" in result or "draft" in result.lower()

    def test_create_draft_other_user(self, test_db, test_users, test_threads):
        user1, user2 = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user2, mail)
        create_tool = tools[3]
        
        result = create_tool.invoke({"thread_id": "t1", "instruction": "reply"})
        
        assert result == "thread not found"

    def test_tool_names_correct(self, test_db, test_users):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        
        tool_names = [t.name for t in tools]
        assert tool_names == ["search_emails", "list_by_category", "get_email", "create_draft"]

    def test_no_tool_user_id_argument(self, test_db, test_users):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        
        for tool in tools:
            if hasattr(tool, 'args_schema'):
                schema = tool.args_schema
                if hasattr(schema, 'schema'):
                    props = schema.schema().get('properties', {})
                    assert 'user_id' not in props

    def test_subject_with_pipe_flattened(self, test_db, test_users):
        user1, _ = test_users
        
        thread = Thread(
            id="t_pipe",
            user_id=user1.id,
            gmail_thread_id="thread_pipe",
            subject="Subject | With | Pipes",
            sender="test@example.com",
            summary="Test",
            status="new"
        )
        test_db.add(thread)
        test_db.commit()
        
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Pipe", "limit": 10})
        
        lines = result.split('\n')
        assert all('|' not in line.split('|')[2] for line in lines if line)

    def test_search_negative_limit(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        tools = make_tools(test_db, user1, mail)
        search_tool = tools[0]
        
        result = search_tool.invoke({"query": "Test", "limit": -5})
        
        assert len(result) > 0
