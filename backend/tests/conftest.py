import pytest

from app import create_app
from config import TestConfig
from extensions import db as _db
from models import Category, BinProvider, BinSchedule


@pytest.fixture
def app():
    """A Flask app instance configured for testing, with tables created."""
    flask_app = create_app(TestConfig)

    with flask_app.app_context():
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """A test client for making requests without running a real server."""
    return app.test_client()


@pytest.fixture
def category(app):
    """A single expense category - most expense/budget tests need at least one."""
    with app.app_context():
        cat = Category(name="Groceries")
        _db.session.add(cat)
        _db.session.commit()
        return {"id": cat.id, "name": cat.name}


@pytest.fixture
def bin_provider(app):
    """A single bin collection provider, used by the bin schedule tests."""
    with app.app_context():
        provider = BinProvider(name="Panda")
        _db.session.add(provider)
        _db.session.commit()
        return {"id": provider.id, "name": provider.name}


@pytest.fixture
def bin_schedule(app, bin_provider):
    """
    A general-waste, weekly collection on Mondays for Eircode prefix 'D02',
    matching the provider from the `bin_provider` fixture - enough seed data
    for the bin lookup endpoints to have something to find.
    """
    with app.app_context():
        schedule = BinSchedule(
            provider_id=bin_provider["id"],
            eircode_prefix="D02",
            bin_type="general",
            collection_weekday=0,  # Monday
            frequency_weeks=1,
        )
        _db.session.add(schedule)
        _db.session.commit()
        return {"id": schedule.id, "provider_id": bin_provider["id"]}


@pytest.fixture
def auth_headers(client):
    """
    Register and log in a brand-new user and return the Authorization header
    every protected endpoint needs. Using a fixture (rather than repeating
    this in every test) keeps each test focused on the behaviour it's
    actually checking.
    """
    client.post("/api/auth/register", json={
        "name": "Test Student",
        "email": "student@example.com",
        "password": "password123",
    })
    login_res = client.post("/api/auth/login", json={
        "email": "student@example.com",
        "password": "password123",
    })
    token = login_res.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
