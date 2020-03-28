from backend import create_app
import pytest


@pytest.fixture(scope='module')
def test_client():
    app = create_app()
    client = app.test_client()
    context = app.app_context()
    context.push()

    yield client
    context.pop()
