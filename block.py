import logging
import time
from base64 import b64encode
import PoS
import wallet
from constants import Constants
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

    def fees(self):
        """
        Calculates the sum of the fees of all transactions. To be used when receiving or creating
        a block to add the resulting amount to the validator.
        :return:
        """
        total_fees = 0
        for tx in self.transactions:
            tx_contents = tx["contents"]

            # print("Current tx:")
            # print("amount: {}".format(tx_contents["amount"]))

            if tx_contents["type"] == TransactionType.MESSAGE.value:
                total_fees += len(tx_contents["message"])
            elif tx_contents["type"] == TransactionType.AMOUNT.value:
                total_fees += tx_contents["amount"] * (Constants.TRANSFER_FEE_MULTIPLIER - 1)

        return total_fees

    def stakes(self):
        stakes = {}
        for tx in self.transactions:
            tx_contents = tx["contents"]

            if tx_contents["type"] == TransactionType.STAKE.value:
                stakes[tx_contents["sender_addr"]] = tx_contents["amount"]

        # print(f"Stakes calculated from block {stakes}.")
        return stakes

    def validate(self, val_pubkey, prev_hash):
        my_hash = b64encode(hash_dict(self.contents())).decode()

        if not my_hash == self.block_hash:
            logging.warning("Block hash mismatch")
            return False
        if not val_pubkey == self.validator:
            logging.warning("Validator mismatch! GOT {} EXP {}".format(self.validator[100:110], val_pubkey[100:110]))
            return False
        if not prev_hash == self.prev_hash:
            logging.warning("Previous hash mismatch")
            return False
        return True

            
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