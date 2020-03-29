from backend import create_app
import pytest
from blockchain import Blockchain
from blockchain.transaction import Transaction


@pytest.fixture(scope='module')
def test_client():
    app = create_app(testing=True)
    client = app.test_client()
    context = app.app_context()
    context.push()

    yield client
    context.pop()


@pytest.fixture(scope='module')
def init_blockchain():
    bc = Blockchain()
    bc.create_genesis_block()
    return bc
