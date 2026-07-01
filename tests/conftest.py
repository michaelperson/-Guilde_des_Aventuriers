import pytest

from guilde_api import create_app
from guilde_api.config import TestConfig


@pytest.fixture
def app():
    application = create_app(TestConfig)
    yield application


@pytest.fixture
def client(app):
    return app.test_client()
