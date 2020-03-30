import pytest

from backend.blockchain import TransactionInput, TransactionOutput, Transaction


@pytest.fixture(scope='module')
def test_trans_ins_outs():
    ins = [
        TransactionInput('0', 10),
        TransactionInput('1', 10)
    ]

    outs = [
        TransactionOutput('mytrans', '321', 15),
        TransactionOutput('mytrans', '123', 5)
    ]

    tx = Transaction('123', '321', 15, ins, outs, 'mytrans')

    return tx, ins, outs