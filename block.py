import time
from base64 import b64encode
import PoS
import wallet
from helper import tx_str, hash_dict, sha256hash
from transaction import TransactionBuilder, verify_tx, TransactionType

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
                "hash": self.block_hash
            }
        else:
            return {
                "prev_hash": self.prev_hash,
                "index": self.idx,
                "timestamp": self.timestamp,
                "validator": self.validator,
                "transactions": self.transactions
            }

    def to_str(self, summarized=True, indent=1):
        tabs = indent * "\t"
        s = tabs + f"prev hash: {self.prev_hash}\n"
        s += tabs + f"hash: {self.block_hash}\n"
        s += tabs +  f"index: {self.idx}\n"
        s += tabs +  f"timestamp: {self.timestamp}\n"
        if summarized:
            s += tabs + f"validator: ...{self.validator[100:110]}...\n"
        else:
            s += tabs + f"validator: {self.validator}\n"
        
        s += tabs + f"transactions: [\n"
        
        for i, tx in enumerate(self.transactions):
            s += tx_str(tx, summarized, indent+1)
            # don't add a newline after the last transaction
            if i != len(self.transactions) - 1:
                s += "\n"
        s += tabs + "]"
        return s


    def hash(self):
        return hash_dict(self.contents())

    def set_hash(self):
        self.block_hash = b64encode(self.hash()).decode()

    def validate(self, val_pubkey, prev_hash):
        my_hash = hash_dict(self.contents())
        if not my_hash == self.block_hash:
            return False
        if not val_pubkey == self.validator:
            return False
        if not prev_hash == self.prev_hash:
            return False
        return True

            
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


if __name__ == "__main__":
    w = wallet.Wallet()
    t = TransactionBuilder(w)
    tx = t.create("some_addr", TransactionType.AMOUNT.value, 1337)
    res = verify_tx(tx)
    if res:
        print("Tx was verified!")

    b = Block("0", time.time(), [tx, tx], "aaaaaa", "0xdeadbeef", block_hash=None)
    
    b.block_hash = b.hash()
    if b.validate():
        print("Block was validated")
    else:
        print("[Error] Block was NOT verified.")