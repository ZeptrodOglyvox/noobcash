from backend.blockchain import Block, Blockchain


def test_block2dict(test_trans_ins_outs):
    tx, ins, outs = test_trans_ins_outs
    block = Block(0, '123456', transactions=[tx, tx])
    block.hash = block.compute_hash()
    assert block.hash == block.compute_hash()

    b_dict = block.to_dict()
    assert all(isinstance(t, dict) for t in b_dict['transactions'])

    block_resurrected = Block.from_dict(b_dict)
    assert block == block_resurrected


def test_blockchain_mine(test_trans_ins_outs):
    bch = Blockchain()
    tx, ins, outs = test_trans_ins_outs

    bch.add_transaction(tx)
    bch.mine()

    assert len(bch.chain) == 2
    assert tx in bch.last_block.transactions
    assert bch.last_block.nonce
    assert bch.last_block.hash.startswith(bch.pow_difficulty * '0')
    assert bch.last_block.previous_hash == bch.chain[0].hash
    assert not bch.unconfirmed_transactions


def test_chain_dump(test_trans_ins_outs):
    bch = Blockchain()
    tx, ins, outs = test_trans_ins_outs
    bch.add_transaction(tx)
    bch.mine()
    dump = bch.json_dump()
    bch_resurrected = Blockchain.from_dump(dump)
    assert not isinstance(bch_resurrected, str)
    assert bch.chain == bch_resurrected.chain
