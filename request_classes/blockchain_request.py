import json

import helper
from block import Block
from blockchain import Blockchain
from transaction import TransactionContents


class BlockchainRequest:
    """
    This is the request made from Boostrap node after bootstrap phase is complete and node list has been sent.
    It contains the blockchain in its current state (essentially a collection of blocks).
    """

    @classmethod
    def from_blockchain_to_request(cls, blockchain: Blockchain):
        request = []
        for block in blockchain.blocks:
            request.append(helper.to_deep_dict(block)) # Encode/Decode hash.
        return request

    @classmethod
    def from_request_to_blocks(cls, request):
        blocks = []
        for block in request:
            transactions_raw = block["transactions"]
            transactions = []
            for transaction in transactions_raw:
                contents = json.loads(transaction)["contents"]  # TODO: Fix json loads.
                contents = json.loads(contents)
                contents = TransactionContents(
                    contents["sender_addr"],
                    contents["recv_addr"],
                    contents["trans_type"],
                    contents["amount"],
                    contents["message"],
                    contents["nonce"]
                )

                transactions.append({
                    "contents": contents,
                    "hash": json.loads(transaction)["hash"],
                    "sign": json.loads(transaction)["sign"]
                })

            blocks.append(Block(
                block["id"],
                block["timestamp"],
                transactions,
                block["validator"],
                block["hash"],
                block["prev_hash"]
            ))
        return blocks