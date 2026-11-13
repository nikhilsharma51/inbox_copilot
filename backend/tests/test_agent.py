import pytest
import sys
from unittest.mock import patch

from langchain_core.messages import AIMessage
from langchain.chat_models.base import BaseChatModel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, User, Thread, Draft
from app.gmail import FakeGmail
from ai_pipeline.agent import run_agent, build_agent
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
    user1, user2 = test_users
    
    t1 = Thread(id="t1", user_id=user1.id, gmail_thread_id="gt1", subject="Test", sender="a@b.com", summary="summary", status="new")
    t2 = Thread(id="t2", user_id=user1.id, gmail_thread_id="gt2", subject="Action", sender="c@d.com", summary="action item", status="new", needs_reply=True)
    t3 = Thread(id="t3", user_id=user2.id, gmail_thread_id="gt3", subject="Other", sender="e@f.com", summary="other user", status="new")
    
    test_db.add_all([t1, t2, t3])
    test_db.commit()
    return t1, t2, t3


class ScriptedChatModel(BaseChatModel):
    model_config = {"arbitrary_types_allowed": True}
    responses: list = []
    call_count: int = 0
    
    def __init__(self, responses: list[AIMessage], **kwargs):
        super().__init__(responses=responses, call_count=0, **kwargs)

    def _generate(self, messages, stop=None, **kwargs):
        raise NotImplementedError("Use invoke instead")

    def _call(self, messages, stop=None, **kwargs):
        raise NotImplementedError("Use invoke instead")

    def invoke(self, input, config=None, **kwargs):
        if self.call_count >= len(self.responses):
            return self.responses[-1]
        response = self.responses[self.call_count]
        self.call_count += 1
        return response

    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self

    @property
    def _identifying_params(self):
        return {}


class TestAgent:
    def test_agent_search_then_answer(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        
        model = ScriptedChatModel([
            AIMessage(
                content="",
                tool_calls=[{"name": "search_emails", "args": {"query": "test"}, "id": "1"}]
            ),
            AIMessage(content="Found emails about test.")
        ])
        
        answer, tool_calls = run_agent(test_db, user1, mail, "Find emails", llm=model)
        
        assert "Found" in answer
        assert "search_emails" in tool_calls

    def test_agent_list_draft_and_answer(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        
        model = ScriptedChatModel([
            AIMessage(
                content="",
                tool_calls=[{"name": "list_by_category", "args": {"category": "action"}, "id": "1"}]
            ),
            AIMessage(
                content="",
                tool_calls=[{"name": "create_draft", "args": {"thread_id": "t2", "instruction": "say yes"}, "id": "2"}]
            ),
            AIMessage(content="Draft created.")
        ])
        
        answer, tool_calls = run_agent(test_db, user1, mail, "Create draft", llm=model)
        
        assert "Draft" in answer
        assert "list_by_category" in tool_calls
        assert "create_draft" in tool_calls
        assert len(mail.sent) == 0

    def test_agent_recursion_limit(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        
        responses = [
            AIMessage(
                content="",
                tool_calls=[{"name": "search_emails", "args": {"query": "x"}, "id": str(i)}]
            )
            for i in range(15)
        ]
        responses.append(AIMessage(content="Should not reach"))
        model = ScriptedChatModel(responses)
        
        answer, tool_calls = run_agent(test_db, user1, mail, "Loop", llm=model)
        
        assert "step limit" in answer.lower()

    def test_agent_cannot_send(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        
        model = ScriptedChatModel([
            AIMessage(content="I cannot send emails; you review and send in the app.")
        ])
        
        answer, _ = run_agent(test_db, user1, mail, "Send email", llm=model)
        assert len(mail.sent) == 0

    def test_agent_tool_names_correct(self, test_db, test_users, test_threads):
        user1, _ = test_users
        mail = FakeGmail()
        
        agent, tools = build_agent(test_db, user1, mail)
        tool_names = [t.name for t in tools]
        
        assert set(tool_names) == {"search_emails", "list_by_category", "get_email", "create_draft"}
        for name in tool_names:
            assert "send" not in name.lower()

    def test_agent_tool_trace_truncates_long_args(self, test_db, test_users, test_threads, capsys):
        user1, _ = test_users
        mail = FakeGmail()
        
        long_arg = "x" * 100
        model = ScriptedChatModel([
            AIMessage(
                content="",
                tool_calls=[{"name": "search_emails", "args": {"query": long_arg}, "id": "1"}]
            ),
            AIMessage(content="Answer")
        ])
        
        answer, _ = run_agent(test_db, user1, mail, "test", llm=model)
        
        captured = capsys.readouterr()
        assert "tool:" in captured.err
        lines = [l for l in captured.err.split("\n") if "tool:" in l]
        if lines:
            assert len(lines[0]) < 200

    def test_agent_user_isolation(self, test_db, test_users, test_threads):
        user1, user2 = test_users
        mail = FakeGmail()
        
        model = ScriptedChatModel([
            AIMessage(
                content="",
                tool_calls=[{"name": "list_by_category", "args": {"category": "action"}, "id": "1"}]
            ),
            AIMessage(content="Your threads")
        ])
        
        answer, _ = run_agent(test_db, user1, mail, "Show threads", llm=model)
        
        threads_u1 = test_db.query(Thread).filter_by(user_id=user1.id).all()
        threads_u2 = test_db.query(Thread).filter_by(user_id=user2.id).all()
        
        assert len(threads_u1) > 0
        assert len(threads_u2) > 0
