import json
import struct
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives import hashes
import wallet

class TransactionBuilder:

    def __init__(self, wallet):
        self.wallet = wallet
        self.nonce = 0
        self.sender_addr = self.wallet.public_key()

    def create(self, recv_addr, trans_type, payload):
        """
        if trans_type == "m", payload must be a string message
        if trans_type == "a", payload must be a float amount 
        """

        if trans_type == "m":
            payload = str(payload)
            payload_str = "message"
        else:
            payload = float(payload)
            payload_str = "amount"

        tx_contents = {
            "sender_addr": self.sender_addr,
            "recv_addr": recv_addr,
            "type": trans_type,
            payload_str: payload,
            "nonce": self.nonce,
        }
        tx_str = json.dumps(tx_contents)
        tx_bytes = struct.pack("!" + str(len(tx_str)) + "s", bytes(tx_str, "ascii"))

        digest = hashes.Hash(hashes.SHA256())
        digest.update(tx_bytes)
        tx_hash = digest.finalize()
        tx_sign = self.wallet.sign(tx_bytes)

        tx = {
            "contents": tx_str,
            "hash": b64encode(tx_hash).decode(),
            "sign": b64encode(tx_sign).decode()
        }

        self.nonce += 1

        return json.dumps(tx)

if __name__ == "__main__":
    w = wallet.Wallet()
    t = TransactionBuilder(w)
    tx = t.create("some_addr", "a", 1337)