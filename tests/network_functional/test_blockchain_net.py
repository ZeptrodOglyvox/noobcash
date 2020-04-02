import requests as req

from backend.blockchain import Block, Blockchain


def test_mine_block_no_competition(nodes, network, test_transaction):
    mine_resp = req.get(nodes[1] + '/blockchain/mine_block')
    block_dict = mine_resp.json()
    block = Block.from_dict(block_dict)
    assert mine_resp.status_code == 200
    assert Blockchain.is_valid_proof(block, block_dict['hash'], 3)

    response = req.post(
        nodes[1] + '/blockchain/add_block?broadcast=1',
        json=block_dict
    )

    assert response.status_code == 200

    for i in range(len(nodes)):
        response = req.get(nodes[i] + '/blockchain/get_chain')
        bc_dict = response.json()
        bc = Blockchain.from_dict(bc_dict)
        assert block in bc

