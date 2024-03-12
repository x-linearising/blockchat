import json
import struct
from enum import Enum
from base64 import b64encode, b64decode
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_ssh_public_key

import wallet
from constants import Constants
from helper import sha256hash, dict_bytes


class TransactionType(Enum):
    AMOUNT = "a"
    MESSAGE = "m"
    STAKE = "s"


class TransactionBuilder:

    def __init__(self, wallet):
        self.wallet = wallet
        self.nonce = 0
        self.sender_addr = self.wallet.public_key

    def create(self, recv_addr: str, trans_type, payload):
        """
        if trans_type == "m", payload must be a string message
        if trans_type == "a" or "s", payload must be a float amount
        """

        if trans_type == TransactionType.MESSAGE.value:
            msg = str(payload)
            amount = None
        else:
            msg = None
            amount = float(payload)

        tx_contents = {
            "sender_addr": self.sender_addr,
            "recv_addr": recv_addr,
            "type": trans_type,
            "amount": amount,
            "message": msg,
            "nonce": self.nonce,
        }

        tx_str = json.dumps(tx_contents)
        tx_bytes = struct.pack("!" + str(len(tx_str)) + "s", bytes(tx_str, "ascii"))

        tx_hash = sha256hash(tx_bytes)
        tx_sign = self.wallet.sign(tx_bytes)

        tx = {
            "contents": tx_contents,
            "hash": b64encode(tx_hash).decode(),
            "sign": b64encode(tx_sign).decode()
        }

        self.nonce += 1

        return tx

def verify_tx(tx, expected_nonce) -> bool:
    tx_bytes = dict_bytes(tx["contents"])
    my_hash = sha256hash(tx_bytes)

    if b64decode(tx["hash"]) != my_hash:
        print("[Received Transaction] Hash mismatch detected!")
        return False

    if tx["contents"]["nonce"] < expected_nonce:
        print("[Received Transaction] Invalid nonce detected: EXP = {} GOT = {} SENDER = {}! (possible replay attack)".format(expected_nonce, tx["contents"]["nonce"], tx["contents"]["sender_addr"][100:110]))
        return False


    sender_pubkey = load_ssh_public_key(bytes(tx["contents"]["sender_addr"], "ascii"))
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
        print("[Received Transaction] Invalid signature detected!")
        return False


def tx_cost(tx_contents, sender_stakes):
    # Transaction Cost
    match tx_contents["type"]:
        case TransactionType.MESSAGE.value:
            transaction_cost = len(tx_contents["message"])
        case TransactionType.AMOUNT.value:
            transaction_cost = tx_contents["amount"] * Constants.TRANSFER_FEE_MULTIPLIER
        case TransactionType.STAKE.value:
            transaction_cost = tx_contents["amount"] - sender_stakes  # This could very well be negative
        case _:
            transaction_cost = None
    return transaction_cost


if __name__ == "__main__":
    w = wallet.Wallet()
    t = TransactionBuilder(w)
    tx = t.create("some_addr", TransactionType.AMOUNT.value, 1337)
    res = verify_tx(tx)
    if res:
        print("Tx was verified!")
