import json
import urllib.parse
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import encrypt_token, decrypt_token
from app.db import Base, User
from app.main import create_app
from app.routes.auth import get_db, _make_session_cookie, _verify_session_cookie


@pytest.fixture(scope="function")
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
    return TestClient(app)


@pytest.fixture
def test_user(test_db):
    from cryptography.fernet import Fernet
    import base64
    key = base64.b64decode("srWrhCu6XlhSER2abmn1rmbWD7VDYLIIsqyhOFkbkfs=")
    cipher = Fernet(key)
    token_enc = cipher.encrypt("test_refresh_token".encode()).decode()
    
    user = User(
        google_sub="test_sub_123",
        email="test@example.com",
        refresh_token_enc=token_enc,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


class TestOAuthState:
    def test_bad_state_rejected(self, client):
        response = client.get("/api/auth/callback?code=test_code&state=wrong_state")
        assert response.status_code == 400
        assert "Invalid or missing state" in response.text

    def test_state_cookie_cleared_after_callback(self, client, test_db):
        response = client.get("/api/auth/login", follow_redirects=False)
        state_value = client.cookies.get("oauth_state")
        assert state_value is not None
        
        with patch("app.routes.auth._exchange_code_for_tokens") as mock_exchange:
            with patch("app.routes.auth._get_user_info") as mock_user_info:
                mock_exchange.return_value = {
                    "access_token": "test_access",
                    "refresh_token": "test_refresh",
                    "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify",
                }
                mock_user_info.return_value = {
                    "sub": "new_sub",
                    "email": "new@example.com",
                }
                
                response = client.get(
                    f"/api/auth/callback?code=test_code&state={state_value}",
                    follow_redirects=False,
                )
                
                assert response.status_code == 302
                assert "oauth_state" in response.cookies
                assert response.cookies["oauth_state"]["max-age"] == 0


class TestGrantedScopes:
    def test_missing_gmail_scopes_rejected(self, client):
        response = client.get("/api/auth/login", follow_redirects=False)
        state_value = client.cookies.get("oauth_state")
        
        with patch("app.routes.auth._exchange_code_for_tokens") as mock_exchange:
            with patch("app.routes.auth._get_user_info") as mock_user_info:
                mock_exchange.return_value = {
                    "access_token": "test_access",
                    "refresh_token": "test_refresh",
                    "scope": "https://www.googleapis.com/auth/userinfo.email",
                }
                mock_user_info.return_value = {
                    "sub": "new_sub",
                    "email": "new@example.com",
                }
                
                response = client.get(
                    f"/api/auth/callback?code=test_code&state={state_value}",
                    follow_redirects=False,
                )
                
                assert response.status_code == 403
                assert "Missing required Gmail scopes" in response.text

    def test_sufficient_scopes_accepted(self, client, test_db):
        response = client.get("/api/auth/login", follow_redirects=False)
        state_value = client.cookies.get("oauth_state")
        
        with patch("app.routes.auth._exchange_code_for_tokens") as mock_exchange:
            with patch("app.routes.auth._get_user_info") as mock_user_info:
                mock_exchange.return_value = {
                    "access_token": "test_access",
                    "refresh_token": "test_refresh",
                    "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify",
                }
                mock_user_info.return_value = {
                    "sub": "new_sub",
                    "email": "new@example.com",
                }
                
                response = client.get(
                    f"/api/auth/callback?code=test_code&state={state_value}",
                    follow_redirects=False,
                )
                
                assert response.status_code == 302
                user = test_db.query(User).filter(User.google_sub == "new_sub").first()
                assert user is not None
                assert user.email == "new@example.com"


class TestSessionCookie:
    def test_cookie_flags_httponly(self, client, test_db):
        response = client.get("/api/auth/login", follow_redirects=False)
        state_value = client.cookies.get("oauth_state")
        
        with patch("app.routes.auth._exchange_code_for_tokens") as mock_exchange:
            with patch("app.routes.auth._get_user_info") as mock_user_info:
                mock_exchange.return_value = {
                    "access_token": "test_access",
                    "refresh_token": "test_refresh",
                    "scope": "https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.modify",
                }
                mock_user_info.return_value = {
                    "sub": "new_sub",
                    "email": "new@example.com",
                }
                
                response = client.get(
                    f"/api/auth/callback?code=test_code&state={state_value}",
                    follow_redirects=False,
                )
                
                assert "session" in response.cookies
                session_cookie = response.cookies["session"]
                assert session_cookie.get("httponly") is True
                assert session_cookie.get("samesite").lower() == "lax"


class TestMeEndpoint:
    def test_me_401_without_cookie(self, client):
        response = client.get("/api/auth/me")
        assert response.status_code == 401
        assert "Not logged in" in response.text

    def test_me_401_with_invalid_cookie(self, client):
        client.cookies.set("session", "invalid_session_token")
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_200_with_valid_cookie(self, client, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user.id
        assert data["email"] == test_user.email
        assert data["google_sub"] == test_user.google_sub


class TestLogout:
    def test_logout_clears_cookie(self, client, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        response = client.post("/api/auth/logout")
        assert response.status_code == 200
        assert "session" in response.cookies
        assert response.cookies["session"]["max-age"] == 0

    def test_logout_401_without_cookie(self, client):
        response = client.post("/api/auth/logout")
        assert response.status_code == 401


class TestDisconnect:
    def test_disconnect_revoke_success(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        with patch("app.routes.auth._revoke_token") as mock_revoke:
            mock_revoke.return_value = None
            
            response = client.post("/api/auth/disconnect")
            assert response.status_code == 200
            data = response.json()
            assert "Disconnected successfully" in data["message"]
            
            test_db.refresh(test_user)
            assert test_user.refresh_token_enc is None

    def test_disconnect_revoke_fails_but_local_cleared(self, client, test_db, test_user):
        session_token = _make_session_cookie(test_user.id)
        client.cookies.set("session", session_token)
        
        with patch("app.routes.auth._revoke_token") as mock_revoke:
            mock_revoke.side_effect = Exception("Network error")
            
            response = client.post("/api/auth/disconnect")
            assert response.status_code == 200
            data = response.json()
            assert "warning" in data
            assert data["warning"] is True
            
            test_db.refresh(test_user)
            assert test_user.refresh_token_enc is None

    def test_disconnect_401_without_cookie(self, client):
        response = client.post("/api/auth/disconnect")
        assert response.status_code == 401


class TestRedirectUri:
    def test_redirect_uri_from_config_only(self, client):
        response = client.get("/api/auth/login", follow_redirects=False)
        assert response.status_code == 302
        
        auth_url = response.headers["Location"]
        parsed = urllib.parse.urlparse(auth_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        from app.config import settings
        assert params["redirect_uri"][0] == settings.oauth_redirect_uri
