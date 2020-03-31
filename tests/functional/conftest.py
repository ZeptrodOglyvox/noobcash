import json

from backend import create_app
import backend as node
import pytest
from backend.blockchain import Blockchain, Wallet, TransactionOutput, Transaction, Block


def assert_json_200(response):
    assert response.content_type == 'application/json'
    assert response.status_code == 200


@pytest.fixture(scope='module')
def test_client():
    app = create_app(testing=True)
    client = app.test_client()
    context = app.app_context()
    context.push()

    yield client
    context.pop()


@pytest.fixture()
def node_setup():
    node.wallet = Wallet()

    node.blockchain = Blockchain()
    node.blockchain.utxos = {}

    address = node.wallet.address
    node.blockchain.utxos[address] = [
        TransactionOutput('0', address, 10),
        TransactionOutput('1', address, 10)
    ]
    node.blockchain.utxos['0'] = []


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


@pytest.fixture()
def signature(test_client, test_transaction):
    response = test_client.post(
        'transactions/sign',
        data=json.dumps(test_transaction.to_dict()),
        content_type='application/json'
    )

    assert response.content_type == 'application/json'
    assert response.status_code == 200
    data = response.get_json()
    return data['signature']


@pytest.fixture()
def test_block(test_client, test_transaction, signature):
    response = test_client.post(
        '/transactions/submit?broadcast=0',
        data=json.dumps(dict(
            transaction=test_transaction.to_dict(),
            signature=signature
        )),
        content_type='application/json'
    )
    assert_json_200(response)

    response = test_client.get('/blockchain/mine_block')
    assert_json_200(response)
    block_dict = response.get_json()
    return Block.from_dict(block_dict)
