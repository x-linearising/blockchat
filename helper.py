import json
import struct
from base64 import b64encode
from socket import gethostname, gethostbyname

from cryptography.hazmat.primitives import hashes


class JSONSerializable:
    """
        Classes inheriting this class can have their instances converted to Json.
        This is useful in endpoints as Flask needs a dictionary like structure
        for its responses and requests.
    """
    def to_dict(self):
        if hasattr(self, '__dict__'):
            return self.__dict__
        else:
            raise TypeError("Object is not JSON serializable")

def myIP():
    # TODO: this may return 127.0.0.1 on some machines instead of the local IP addr.
    # no problem when running locally, but we don't want our online nodes to believe
    # 127.0.0.1 is their IP
    return gethostbyname(gethostname())


def sha256hash(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()


def string_to_bytes(string: str) -> bytes:
    return struct.pack("!" + str(len(string)) + "s", bytes(string, "ascii"))


def to_deep_dict(obj):
    if isinstance(obj, dict):
        return {k: to_deep_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dict__'):
        return to_deep_dict(vars(obj))
    elif isinstance(obj, list):
        return [to_deep_dict(item) for item in obj]
    else:
        return obj


class Hashable:
    # Could make a constructor that initializes hash.

    def get_as_bytes(self) -> bytes:
        return string_to_bytes(self.get_hashable_part_as_string())

    def get_hashable_part_as_string(self) -> str:
        return json.dumps(self.get_hashable_part_as_dict())

    def get_hash(self):
        return b64encode(sha256hash(self.get_as_bytes())).decode()

    def get_hashable_part_as_dict(self):
        return to_deep_dict(self)






