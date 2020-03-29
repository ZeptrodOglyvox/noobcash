import json

from backend import create_app
import backend as node
import pytest
from backend.blockchain import Blockchain, Wallet, TransactionOutput, Transaction


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


@pytest.fixture()
def node_setup():
    node.wallet = Wallet()
    address = node.wallet.address
    node.utxos[address] = [
        TransactionOutput('0', address, 10),
        TransactionOutput('1', address, 10)
    ]


@pytest.fixture()
def test_transaction(node_setup, test_client):
    response = test_client.post(
        '/transactions/create',
        data=json.dumps(dict(
            sender_address=node.wallet.address,
            recipient_address='0',
            amount=15
        )),
        content_type='application/json'
    )

    assert response.content_type == 'application/json'
    assert response.status_code == 200
    data = response.get_json()
    return Transaction.from_dict(data)