import json
from block import Block

class BlockchainRequest:
    """
    This is the request made from Boostrap node after bootstrap phase is complete and node list has been sent.
    It contains the blockchain in its current state (essentially a collection of blocks).
    """

    @classmethod
    def from_blockchain_to_request(cls, blockchain):
        request = [block.contents(include_hash=True) for block in blockchain.blocks]
        return request

    @classmethod
    def from_request_to_blocks(cls, request):
        blocks = []
        for block in request:
            # Read the block's transactions...
            block_txs = block["transactions"]
            # ...and parse them into this list
            transactions = []
            for tx in block_txs:
                tx_contents = tx["contents"]
                tx_hash = tx["hash"]
                tx_sign = tx["sign"]
                contents = {
                    "sender_addr": tx_contents["sender_addr"],
                    "recv_addr": tx_contents["recv_addr"],
                    "type": tx_contents["type"],
                    "amount": tx_contents["amount"],
                    "message": tx_contents["message"],
                    "nonce": tx_contents["nonce"]
                }
                transactions.append({
                    "contents": contents,
                    "hash": tx_hash,
                    "sign": tx_sign
                })

            blocks.append(Block(
                block["index"],
                block["timestamp"],
                transactions,
                block["validator"],
                block["prev_hash"],
                block["hash"]
            ))
        return blocks