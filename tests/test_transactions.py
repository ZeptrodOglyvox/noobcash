import binascii

import pytest
from Crypto.PublicKey import RSA

from tests.utils import assert_json_200


def test_generate_wallet(test_client):
    response = test_client.get('/transactions/generate_wallet')
    data = response.get_json()

    assert_json_200(response)
    private_key = RSA.import_key(binascii.unhexlify(data['private_key']))
    public_key = RSA.import_key(binascii.unhexlify(data['public_key']))
    assert private_key.publickey() == public_key

    from backend import wallet
    assert wallet is not None


def test_required_fields(test_client):
    def assert_missing(r):
        data = response.get_json()
        assert r.content_type == 'application/json'
        assert r.status_code == 400
        assert data['message'] == 'Required fields missing.'

    response = test_client.post('/transactions/create')
    assert_missing(response)

    response = test_client.post('/transactions/create',  data={'sender_address': 5})
    assert_missing(response)

