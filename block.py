import time
import json
import struct
from base64 import b64encode
from cryptography.hazmat.primitives import hashes
import PoS
from constants import Constants
import wallet
from helper import Hashable, hash_dict
from transaction import TransactionBuilder, verify_tx


def sha256hash(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()

def create_hash(data):
    # convert dictionary to json string
    block_str = json.dumps(data)
    # convert json to bytes and deal with endianness
    block_bytes = struct.pack("!" + str(len(block_str)) + "s", bytes(block_str, "ascii"))
    # create the sha256 hash of the block
    block_hash = sha256hash(block_bytes)
    # return
    return b64encode(block_hash).decode()

"""
Genesis block contains id=0, validator=0, previous_hash=1
and is not validated!
"""
class Block():
    def __init__(self, idx, timestamp, transactions, validator, prev_hash, block_hash=None):
        self.idx = idx
        self.timestamp = timestamp
        self.transactions = transactions
        self.validator = validator
        self.block_hash = block_hash
        self.prev_hash = prev_hash

    def contents(self):
        return {
            "index": self.idx,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "validator": self.validator,
            "prev_hash": self.prev_hash
        }

    def hash(self):
        return hash_dict(self.contents())

    def validate(self):
        my_hash = hash_dict(self.contents())
        return my_hash == self.block_hash
            
    @classmethod
    def construct_genesis_block(cls, tx_builder: TransactionBuilder):
        block = cls(id=0,
                    timestamp=time.time(),
                    transactions=[tx_builder.create_genesis_transaction()],
                    validator=Constants.BOOTSTRAP_ID,
                    hash=None,
                    prev_hash=1)
        block.hash = block.get_hash()  # Watch out, has not been encoded/decoded.
        return block


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

# kathe node lambanei minima oti brethike o validator
def validate_block(validator_node, new_block):

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
