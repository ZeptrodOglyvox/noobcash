import pytest
import requests as req

from backend.blockchain import Transaction


@pytest.fixture()
def nodes():
    nodes = [
        'http://127.0.0.1:5000',
        'http://127.0.0.1:5001',
        'http://127.0.0.1:5002'
    ]

    for url in nodes:
        req.get(url + '/clear')

    yield nodes

    for url in nodes:
        req.get(url + '/clear')


@pytest.fixture()
def get_info(nodes):
    def wrapper(node_id):
        resp = req.get(nodes[node_id] + '/get_info')
        assert resp.status_code == 200
        return resp.json()
    return wrapper


@pytest.fixture()
def bootstrap(nodes):
    response = req.post(nodes[0] + '/setup_bootstrap', json=dict(initial_amount=300))
    assert response.status_code == 200


@pytest.fixture()
def network(nodes, bootstrap, get_info):
    for i in range(1, len(nodes)):
        req.get(nodes[i] + '/generate_wallet').json()
        req.post(nodes[i] + '/register', json=dict(bootstrap_address=nodes[0]))

    resp = req.get(nodes[0] + '/setup_network')
    assert resp.status_code == 200
    info = get_info(0)
    return info['network']


@pytest.fixture()
def test_transaction(nodes, network):
    response = req.post(
        nodes[0] + '/transactions/create',
        json=dict(
            sender_address=network[0]['public_key'],
            recipient_address=network[1]['public_key'],
            amount=10
        )
    )

    tx_dict = response.json()
    response = req.post(
        nodes[0] + '/transactions/sign',
        json=tx_dict
    )
    data = response.json()
    signature = data['signature']
    response = req.post(
        nodes[0] + '/transactions/submit?broadcast=1',
        json=dict(
            transaction=tx_dict,
            signature=signature
        )
    )

    return Transaction.from_dict(tx_dict)
