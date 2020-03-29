import backend as node
from backend.blockchain import Wallet, TransactionOutput, TransactionInput, Transaction


def test_wallet():
    w = Wallet()
    assert w.private_key_rsa.publickey() == w.public_key_rsa


def test_wallet_balance():
    node.wallet = Wallet()
    address = node.wallet.address
    node.utxos[address] = [
        TransactionOutput('0', address, 15),
        TransactionOutput('1', address, 12)
    ]

    assert node.wallet.balance() == 27


def test_transaction_dictification():
    ins = [
        TransactionInput('0', 10),
        TransactionInput('1', 10)
    ]

    outs = [
        TransactionOutput('mytrans', '321', 15),
        TransactionOutput('mytrans', '123', 5)
    ]

    tx = Transaction('123', '321', 15, ins, outs, 'mytrans')

    tx_dict = tx.to_dict()
    assert tx_dict['transaction_inputs'] == [t.to_dict() for t in ins]
    assert tx_dict['transaction_outputs'] == [t.to_dict() for t in outs]

    tx_ressurection = Transaction.from_dict(tx_dict)

    assert tx_ressurection == tx
    assert tx_ressurection.transaction_outputs == outs
    assert tx_ressurection.transaction_inputs == ins
