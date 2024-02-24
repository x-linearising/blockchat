from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class Wallet:

    def __init__(self):
        self._key_obj = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self \
            ._key_obj \
            .public_key() \
            .public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH) \
            .decode()

    def sign(self, msg: bytes) -> bytes:
        signature = self._key_obj.sign(
            msg,
            padding.PSS(
                mgf = padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def verify(self, signature: bytes, msg: bytes) -> bool:
        try:
            self._key_obj.public_key().verify(
                signature,
                msg,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except InvalidSignature:
            return False