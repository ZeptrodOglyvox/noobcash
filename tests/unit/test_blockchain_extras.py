import backend as node
from backend.blockchain import Wallet, TransactionOutput, TransactionInput, Transaction, verify_signature


def test_wallet():
    w = Wallet()
    assert w.private_key_rsa.publickey() == w.public_key_rsa


def test_wallet_balance():
    node.wallet = Wallet()
    address = node.wallet.address
    node.blockchain.utxos[address] = [
        TransactionOutput('0', address, 15),
        TransactionOutput('1', address, 12)
    ]

    assert node.wallet.balance() == 27


def test_transaction_dictification(test_trans_ins_outs):
    tx, ins, outs = test_trans_ins_outs

    tx_dict = tx.to_dict()
    assert tx_dict['transaction_inputs'] == [t.to_dict() for t in ins]
    assert tx_dict['transaction_outputs'] == [t.to_dict() for t in outs]

    tx_ressurection = Transaction.from_dict(tx_dict)

    assert tx_ressurection == tx
    assert tx_ressurection.transaction_outputs == outs
    assert tx_ressurection.transaction_inputs == ins


def test_verify_signature():
    w = Wallet()
    tx = Transaction(w.address, '0', 0)
    signature = tx.sign(w.private_key_rsa)
    assert verify_signature(tx, signature)
