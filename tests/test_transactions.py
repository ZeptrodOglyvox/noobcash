import binascii

import pytest
from Crypto.PublicKey import RSA


def test_generate_wallet(test_client):
    response = test_client.get('/transactions/generate_wallet')
    data = response.get_json()

    assert response.content_type == 'application/json'
    assert response.status_code == 200
    private_key = RSA.import_key(binascii.unhexlify(data['private_key']))
    public_key = RSA.import_key(binascii.unhexlify(data['public_key']))
    assert private_key.publickey() == public_key
