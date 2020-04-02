import pytest
import requests as req


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
    response = req.get(nodes[0] + '/setup_bootstrap')
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
