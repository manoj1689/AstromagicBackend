import pytest
from fastapi.testclient import TestClient
from main import app  
from services.auth import get_current_user
from db.session import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base

# Mock database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Dependency override for test
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db


client = TestClient(app)

@pytest.fixture
def mock_user():
    return {
        "id": 1,
        "username": "test_user",
        "email": "test@example.com",
        "is_active": True
    }

def test_astrology_chat_success(monkeypatch, mock_user):
    def mock_get_current_user():
        return mock_user

    def mock_get_db():
        class MockDBSession:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockDBSession()

    monkeypatch.setattr("services.auth.get_current_user", mock_get_current_user)
    monkeypatch.setattr("db.session.get_db", mock_get_db)

    # Sample input
    payload = {
        "scenario_id": 1,
        "user_details": {
            "date_of_birth": "1990-01-01",
            "time_of_birth": "10:30 AM",
            "place_of_birth": "New Delhi"
        },
        "user_query": "Tell me about my career prospects.",
        "chat_history": [
            {"user": "Hello!", "bot": "Hi, how can I assist you with astrology today?"}
        ]
    }

    response = client.post("/api/v1/chat/astrology/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "detailed_timeline" in data
    assert "astrological_insights" in data
    assert "remedies" in data

def test_astrology_chat_invalid_scenario(monkeypatch, mock_user):
    def mock_get_current_user():
        return mock_user

    def mock_get_db():
        class MockDBSession:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockDBSession()

    monkeypatch.setattr("services.auth.get_current_user", mock_get_current_user)
    monkeypatch.setattr("db.session.get_db", mock_get_db)

    payload = {
        "scenario_id": 999,  
        "user_details": {
            "date_of_birth": "1990-01-01",
            "time_of_birth": "10:30 AM",
            "place_of_birth": "New Delhi"
        },
        "user_query": "Tell me about my career prospects.",
        "chat_history": []
    }

    response = client.post("/api/v1/chat/astrology/chat", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Scenario not found."
