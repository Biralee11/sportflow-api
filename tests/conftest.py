import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
from config import TEST_DATABASE_URL

# Tests run against a separate database so they never touch development data.
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redirects every endpoint's get_db dependency to the test database during tests.
# The application code is unchanged - FastAPI transparently swaps the dependency.
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    # Fresh schema before each test, dropped after, so tests are fully isolated
    # and never leak state into one another.
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    # Depends on db_session so the tables exist before any request is made.
    return TestClient(app)

@pytest.fixture
def admin_token(client, db_session):
    # Admins cannot self-register through the public API, so tests seed one directly
    # into the test database (the same bootstrap problem seed.py solves in production),
    # then log in to obtain a real token for exercising admin-only endpoints.
    from models.models import UserModel
    from services.auth_service import hash_password, create_access_token
    from database import Base
    from sqlalchemy.orm import Session
    
    db = TestSessionLocal()
    admin = UserModel(
        email="admin@test.com",
        hashed_password=hash_password("AdminPass1!"),
        first_name="Admin",
        last_name="Test",
        role="admin"
    )
    db.add(admin)
    db.commit()
    db.close()
    
    login_response = client.post("/auth/login", json={
        "email": "admin@test.com",
        "password": "AdminPass1!"
    })
    return login_response.json()["access_token"]
