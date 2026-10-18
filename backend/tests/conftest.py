import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app  # noqa: E402
from config import TestConfig  # noqa: E402
from extensions import db  # noqa: E402
from seed import seed  # noqa: E402


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def configured_gemini(app):
    """Pretend a Gemini key is configured (the model call is monkeypatched per test)."""
    app.config["GEMINI_API_KEY"] = "test-key"
    return app
