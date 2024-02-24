import time
import json
import struct
from base64 import b64encode
from cryptography.hazmat.primitives import hashes
import PoS
from constants import Constants
import wallet
from helper import Hashable, hash_dict, sha256hash
from transaction import TransactionBuilder, verify_tx


class Block():
    def __init__(self, idx, timestamp, transactions, validator, prev_hash, block_hash=None):
        self.idx = idx
        self.timestamp = timestamp
        self.transactions = transactions
        self.validator = validator
        self.block_hash = block_hash
        self.prev_hash = prev_hash

    def contents(self, include_hash=False):
        if include_hash:
            return {
                "prev_hash": self.prev_hash,
                "index": self.idx,
                "timestamp": self.timestamp,
                "validator": self.validator,
                "transactions": self.transactions,
                "hash": b64encode(self.block_hash).decode()
            }
        else:
            return {
                "prev_hash": self.prev_hash,
                "index": self.idx,
                "timestamp": self.timestamp,
                "validator": self.validator,
                "transactions": self.transactions
            }

    def hash(self):
        return hash_dict(self.contents())

    def validate(self):
        my_hash = hash_dict(self.contents())
        return my_hash == self.block_hash
            
    """
        theoro oti to transaction list exei ginei validate apo ton current node
        kapws prepei na ferw to blockchain = list of blocks
    """

def mint_block(node, transactions, capacity, blockchain):
    # if the number of transactions has reached to max block capacity, node runs proof of stake
    if len(transactions) == capacity:
        strategy = PoS(PoS.stakes)
        cur_block_validator = strategy.select_validator()
        # if the current node is the block validator
        if node.id == cur_block_validator:
            # create the new block
            new_block = Block(blockchain[-1], transactions, node)
            # insert it to blockchain (list of all blocks)
            blockchain.append(new_block)

# validator node broadcasts new block to all other nodes
def broadcast_block(validator_node, new_block):

    return

if __name__ == "__main__":
    w = wallet.Wallet()
    t = TransactionBuilder(w)
    tx = t.create("some_addr", "a", 1337)
    res = verify_tx(tx)
    if res:
        print("Tx was verified!")

    b = Block("0", time.time(), [tx, tx], "aaaaaa", "0xdeadbeef", block_hash=None)
    
    b.block_hash = b.hash()
    if b.validate():
        print("Block was validated")
    else:
        print("[Error] Block was NOT verified.")
