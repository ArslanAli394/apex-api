"""
Pytest configuration and fixtures for the test suite.
"""

import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.config import settings


# Override database for testing
TEST_DATABASE_URL = "postgresql://apex_user:apex_password@localhost:5432/apex_test_db"


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_db(test_engine):
    """Create test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(test_db: Session):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_item_data():
    """Sample item data for testing."""
    return {
        "name": "Test Item",
        "description": "Test Description",
        "category": "test",
        "status": "active",
        "created_by": "test_user",
        "metadata": {"key": "value"},
    }


@pytest.fixture
def multiple_items_data():
    """Multiple items for batch testing."""
    return [
        {
            "name": f"Item {i}",
            "description": f"Description {i}",
            "category": "test",
            "status": "active",
            "created_by": "test_user",
        }
        for i in range(5)
    ]
