import pytest

from backend.blockchain import TransactionInput, TransactionOutput, Transaction


@pytest.fixture(scope='module')
def test_trans_ins_outs():
    ins = [
        TransactionInput('0', 10),
        TransactionInput('1', 10)
    ]

    outs = []

    tx = Transaction('123', '321', 15, ins, outs, 'mytrans')

    return tx, ins, outs
