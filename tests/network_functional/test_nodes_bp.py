import backend as node
import requests as req

from backend import Blockchain


def test_generate_wallet(nodes):
    wallet_response = req.get(nodes[0] + '/generate_wallet')
    wallet_data = wallet_response.json()
    assert wallet_data['public_key']
    assert wallet_data['private_key']

    node_response = req.get(nodes[0] + '/get_info')
    node_data = node_response.json()
    assert node_data['public_key'] == wallet_data['public_key']


def test_setup_bootstrap(nodes, get_info, bootstrap):
    info = get_info(0)

    assert info['node_id'] == 0
    assert info['chain_length'] == 1
    assert info['public_key']
    assert len(info['network']) == 1
    assert info['balance'] == 300


def test_register_node(nodes, bootstrap, get_info):
    response = req.post(
        nodes[0] + '/register_node',
        json=dict(
            ip='http://0.0.0.0',
            port=6001,
            wallet_public_key='123'
        )
    )
    assert response.status_code == 200
    assert response.json()['node_id'] == 1


def test_full_registration(nodes, bootstrap, get_info):
    wallet_resp = req.get(nodes[1] + '/generate_wallet')
    assert wallet_resp.status_code == 200

    response = req.post(
        nodes[1] + '/register',
        json=dict(
            bootstrap_address=nodes[0]
        )
    )
    assert response.status_code == 200

    info = get_info(1)
    assert info['node_id'] == 1


def test_setup_node(nodes, get_info):
    bc = Blockchain()
    nw = [dict(id=5, ip='0.0.0.0:6666', public_key='123')]
    response = req.post(
        nodes[1] + '/setup_node',
        json=dict(
            network=nw,
            blockchain=bc.to_dict()
        )
    )
    assert response.status_code == 200

    info = get_info(1)
    assert info['chain_length'] == 1
    assert info['network'] == nw


def test_setup_network(nodes, bootstrap, get_info):
    expected_network = [dict(
        id=0,
        ip='http://127.0.0.1:5000/',
        public_key=get_info(0)['public_key']
    )]

    for i in range(1, len(nodes)):
        wallet = req.get(nodes[i] + '/generate_wallet').json()
        req.post(nodes[i] + '/register', json=dict(bootstrap_address=nodes[0]))
        expected_network.append(dict(
            id=i,
            ip=f'http://127.0.0.1:{5000+i}/',
            public_key=wallet['public_key'])
        )

    response = req.get(nodes[0] + '/setup_network')
    assert response.status_code == 200
    for i in range(0, len(nodes)):
        info = get_info(i)
        assert info['chain_length'] == 1
        assert len(info['network']) == 3
        assert info['network'] == expected_network
