import binascii
import json

from Crypto.PublicKey import RSA

from backend.blockchain import Transaction, TransactionInput, TransactionOutput, verify_signature
import backend as node


def assert_json_200(response):
    assert response.content_type == 'application/json'
    assert response.status_code == 200


def test_required_fields(test_client):
    response = test_client.post('/transactions/create')
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert response.status_code == 400
    assert data['message'] == 'Please submit data as JSON using a POST request.'

    response = test_client.post(
        '/transactions/create',
        data=json.dumps(dict(
            sender_address='0'
        )),
        content_type='application/json'
    )
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert response.status_code == 400
    assert data['message'] == 'Required fields missing.'


def test_create_transaction(test_client, node_setup):
    response = test_client.post(
        '/transactions/create',
        json=dict(
            sender_address=node.wallet.address,
            recipient_address='0',
            amount=15
        )
    )

    assert_json_200(response)
    data = response.get_json()
    tx = Transaction.from_dict(data)

    assert tx.amount == 15
    assert tx.sender_address == node.wallet.address
    assert tx.recipient_address == '0'
    assert len(tx.transaction_inputs) == 2
    assert len(tx.transaction_outputs) == 2
    assert sum(ti.amount for ti in tx.transaction_inputs) == 20
    assert sum(to.amount for to in tx.transaction_outputs) == 20
    assert tx.transaction_outputs[0].recipient_address == '0'
    assert tx.transaction_outputs[1].recipient_address == node.wallet.address


def test_sign_transaction(test_client, node_setup, test_transaction):
    response = test_client.post(
        'transactions/sign',
        data=json.dumps(test_transaction.to_dict()),
        content_type='application/json'
    )

    assert_json_200(response)
    data = response.get_json()
    signature = data['signature']
    assert not isinstance(verify_signature(test_transaction, signature), str)


def test_submit_transaction(test_client, node_setup, test_transaction):
    response = test_client.post(
        'transactions/sign',
        data=json.dumps(test_transaction.to_dict()),
        content_type='application/json'
    )
    assert_json_200(response)
    data = response.get_json()
    signature = data['signature']

    response = test_client.post(
        'transactions/submit?broadcast=0',
        data=json.dumps(dict(
            transaction=test_transaction.to_dict(),
            signature=signature
        )),
        content_type='application/json'
    )

    assert_json_200(response)
    data = response.get_json()
    assert data['message'] == 'Transaction added.'
    assert test_transaction in node.blockchain.unconfirmed_transactions
    assert test_transaction.transaction_outputs[0] in node.blockchain.utxos[test_transaction.recipient_address]
    assert test_transaction.transaction_outputs[1] in node.blockchain.utxos[test_transaction.sender_address]
