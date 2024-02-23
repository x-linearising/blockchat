import time
import json
import struct
from base64 import b64encode
from cryptography.hazmat.primitives import hashes
import PoS

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
class block:
    def __init__(self, prev_block, transactions, cur_node, is_genesis=0):
        self.id = 0 if is_genesis else prev_block.id + 1
        self.timestamp = time.time()
        self.transactions = transactions
        self.to_hash = {
            'id': self.id,
            'timestamp': time.time(),
            'transactions': self.transactions,
        }
        self.hash = create_hash(self.to_hash)
        self.prev_hash = 1 if is_genesis else prev_block.hash
        self.validator = 0 if is_genesis else cur_node # current node's publc key

    """
        theoro oti to transaction list exei ginei validate apo ton current node
        kapws prepei na ferw to blockchain = list of blocks
    """

def mint_block(node, transactions, capacity, blockchain):
    # if the number of transactions has reached to max block capacity, node runs proof of stake
    if len(transactions) == capacity:
        strategy = PoS(stakes)
        cur_block_validator = strategy.select_validator()
        # if the current node is the block validator
        if node.id == cur_block_validator:
            # create the new block
            new_block = block(blockchain[-1], transactions, node)
            # insert it to blockchain (list of all blocks)
            blockchain.append(new_block)

# validator node broadcasts new block to all other nodes
def broadcast_block(validator_node, new_block):

    return

# kathe node lambanei minima oti brethike o validator
def validate_block(validator_node, new_block):

    return
