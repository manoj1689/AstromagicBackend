import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from db.models.user import User
from db.base import Base
from db.session import get_db


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

# Test for existing user login
def test_google_signin_existing_user():
    # Arrange: Add a mock user in the database
    db = next(override_get_db())
    mock_user = User(user_id="123", device_id="mock_device", name="Mock User", email="mock@example.com")
    db.add(mock_user)
    db.commit()
    
    # Act: Make a POST request to /google_signin
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "mock_device",
            "name": "Mock User",
            "email": "mock@example.com"
        }
    )

    # Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "access_token" in data["data"]
    assert data["data"]["user_id"] == "123"

# Test for new user registration
def test_google_signin_new_user():
    # Act: Make a POST request to /google_signin with a new device_id
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "new_device",
            "name": "New User",
            "email": "newuser@example.com"
        }
    )

    # Assert: Check the response
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "User registered and login successful"
    assert "access_token" in data["data"]
    assert "user_id" in data["data"]

    # Verify the user is added in the mock database
    db = next(override_get_db())
    user = db.query(User).filter(User.device_id == "new_device").first()
    assert user is not None
    assert user.name == "New User"
    assert user.email == "newuser@example.com"

# Test for missing required fields
def test_google_signin_missing_fields():
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "missing_name_and_email"
        }
    )
    assert response.status_code == 422

# Test for invalid email format
def test_google_signin_invalid_email():
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "invalid_email",
            "name": "Invalid Email User",
            "email": "invalid_email_format"
        }
    )
    assert response.status_code == 422

# Test for duplicate user registration
def test_google_signin_duplicate_user():
    # Arrange: Add a mock user in the database
    db = next(override_get_db())
    mock_user = User(user_id="duplicate_user", device_id="duplicate_device", name="Duplicate User", email="duplicate@example.com")
    db.add(mock_user)
    db.commit()
    
    # Act: Try to register with the same email
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "new_device_for_duplicate_email",
            "name": "Duplicate User New Device",
            "email": "duplicate@example.com"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already in use"

# Test for invalid device ID format
def test_google_signin_invalid_device_id():
    response = client.post(
        "/api/v1/login/google_signin",
        json={
            "device_id": "",
            "name": "Invalid Device ID",
            "email": "valid@example.com"
        }
    )
    assert response.status_code == 422