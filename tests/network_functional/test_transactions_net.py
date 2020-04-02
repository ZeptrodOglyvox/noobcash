import requests as req
import backend as node
from backend import Blockchain
from backend.blockchain import Transaction


def test_create_transaction(nodes, network):
    # Create document
    response = req.post(
        nodes[0] + '/transactions/create',
        json=dict(
            sender_address=network[0]['public_key'],
            recipient_address=network[1]['public_key'],
            amount=10
        )
    )
    assert response.status_code == 200
    tx_dict = response.json()
    tx = Transaction.from_dict(tx_dict)
    assert any(to.amount == 10 for to in tx.transaction_outputs)
    assert any(to.amount == 290 for to in tx.transaction_outputs)

    # Sign document
    response = req.post(
        nodes[0] + '/transactions/sign',
        json=tx_dict
    )
    assert response.status_code == 200
    data = response.json()
    signature = data['signature']

    # Submit to blockchain
    response = req.post(
        nodes[0] + '/transactions/submit?broadcast=1',
        json=dict(
            transaction=tx_dict,
            signature=signature
        )
    )
    assert response.status_code == 200

    # Test if it reached the others
    for i in range(0, 2):
        response = req.get(nodes[i] + '/blockchain/get_chain')
        assert response.status_code == 200

        bc_dict = response.json()
        bc = Blockchain.from_dict(bc_dict)
        assert tx in bc.unconfirmed_transactions
        for to in tx.transaction_outputs:
            assert to in bc.utxos[to.recipient_address]
