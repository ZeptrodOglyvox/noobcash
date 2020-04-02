import binascii

from Crypto.PublicKey import RSA

import backend as node


def test_get_info(test_client, node_setup):
    response = test_client.get('/get_info')
    data = response.json

    expected = dict(
        node_id=node.node_id,
        public_key=node.wallet.public_key,
        chain_length=len(node.blockchain),
        balance=node.wallet.balance(),
        network=node.network
    )

    for k in expected:
        assert data.get(k) is not None
        assert expected[k] == data[k]


def test_generate_wallet(test_client):
    response = test_client.get('/generate_wallet')
    data = response.get_json()

    assert response.status_code == 200
    private_key = RSA.import_key(binascii.unhexlify(data['private_key']))
    public_key = RSA.import_key(binascii.unhexlify(data['public_key']))
    assert private_key.publickey() == public_key

    from backend import wallet
    assert wallet is not None
    assert wallet.private_key_rsa.publickey() == wallet.public_key_rsa