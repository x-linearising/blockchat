import json
from base64 import b64encode, b64decode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from enum import Enum

import helper
import wallet
from constants import Constants


class TransactionType(Enum):
    AMOUNT = "a"
    MESSAGE = "m"


class TransactionContents(helper.Hashable):
    def __init__(self, sender_addr, recv_addr, trans_type, amount, message, nonce):
        self.sender_addr = sender_addr
        self.recv_addr = recv_addr
        self.trans_type = trans_type
        self.amount = amount
        self.message = message
        self.nonce = nonce


class TransactionBuilder:

    def __init__(self, wallet):
        self.wallet = wallet
        self.nonce = 0
        self.sender_addr = self.wallet.public_key

    def create(self, recv_addr: str, trans_type, payload):
        """
        if trans_type == "m", payload must be a string message
        if trans_type == "a", payload must be a float amount 
        """

        if trans_type == TransactionType.MESSAGE.value:
            payload = str(payload)
        else:
            payload = float(payload)

        tx_contents = TransactionContents(
            self.sender_addr,
            recv_addr,
            trans_type,
            payload if trans_type == TransactionType.AMOUNT.value else None,
            payload if trans_type == TransactionType.MESSAGE.value else None,
            self.nonce
        )

        tx_sign = self.wallet.sign(tx_contents.get_as_bytes())

        tx = {
            "contents": tx_contents.get_hashable_part_as_string(),
            "hash": tx_contents.get_hash(),
            "sign": b64encode(tx_sign).decode()
        }

        self.nonce += 1

        return json.dumps(tx)

    # TODO: No need for this to be a separate method? Move this to Bootstrap?
    def create_genesis_transaction(self):
        # TODO: ID or address here?
        return self.create(Constants.BOOTSTRAP_ID,
                           TransactionType.AMOUNT.value,
                           Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES)


def verify_tx(tx: str) -> bool:
    tx = json.loads(tx)
    tx_bytes = helper.string_to_bytes(tx["contents"])
    my_hash = helper.sha256hash(tx_bytes)
    tx["hash"] = b64decode(tx["hash"])

    if tx["hash"] != my_hash:
        print("Hash mismatch detected!")
        return False

    tx["contents"] = json.loads(tx["contents"])
    sender_pubkey = load_pem_public_key(bytes(tx["contents"]["sender_addr"], "ascii"))
    sign = b64decode(tx["sign"])

    try:
        sender_pubkey.verify(
            sign,
            tx_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except InvalidSignature: 
        print("Invalid signature detected!")
        return False


if __name__ == "__main__":
    w = wallet.Wallet()
    t = TransactionBuilder(w)
    tx = t.create("some_addr", "a", 1337)
    res = verify_tx(tx)
    if res:
        print("Tx was verified!")
