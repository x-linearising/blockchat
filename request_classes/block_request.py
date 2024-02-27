from block import Block


class BlockRequest:
    """
    This is the request made from validator node.
    It contains the block.
    """

    @classmethod
    def from_block_to_request(cls, block):
        request = block.contents(include_hash=True)
        return request

    @classmethod
    def from_request_to_block(cls, request):
        # Read the block's transactions...
        block_txs = request["transactions"]
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

        return (Block(
            request["index"],
            request["timestamp"],
            transactions,
            request["validator"],
            request["prev_hash"],
            request["hash"]
        ))
