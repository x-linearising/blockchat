import json
import struct
from socket import gethostname, gethostbyname
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.primitives.serialization import load_ssh_public_key

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

def read_pubkey(path):
    with open(path, "rb") as f:
        k = load_ssh_public_key(f.read()) \
            .public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH) \
            .decode()
        return k


def sha256hash(data: bytes) -> bytes:
    digest = hashes.Hash(hashes.SHA256())
    digest.update(data)
    return digest.finalize()

def dict_bytes(d: dict) -> bytes:
    """ Converts a dict to bytes, forcing big-endian """
    d_str = json.dumps(d)
    d_bytes = struct.pack("!" + str(len(d_str)) + "s", bytes(d_str, "ascii"))
    return d_bytes

def hash_dict(d: dict) -> bytes:
    d_bytes = dict_bytes(d)
    d_hash = sha256hash(d_bytes)
    return d_hash

def tx_str(tx, summarized=True, indent=1):
    """
    Pretty prints a transaction tx, represented as a dict, with indent leading tabs.
    If summarized is set, prints the characters at indexes 100 to 110 for strings
    that are expected to be multi-line (signatures, public keys)
    """
    tabs = indent * "\t"
    s = tabs + "hash: {}\n".format(tx["hash"])
    if summarized:
        s += tabs + "sign: ...{}...\n".format(tx["sign"][100:110]) 
        s += tabs + "sender_addr: ...{}...\n".format(tx["contents"]["sender_addr"][100:110])
        s += tabs + "recv_addr: ...{}...\n".format(tx["contents"]["recv_addr"][100:110])
    else:   
        s += tabs + "sign: {}\n".format(tx["sign"])
        s += tabs + "sender_addr: {}\n".format(tx["contents"]["sender_addr"])
        s += tabs + "recv_addr: {}\n".format(tx["contents"]["recv_addr"])
    
    s += tabs + "type: {}\n".format(tx["contents"]["type"])
    s += tabs + "amount: {}\n".format(tx["contents"]["amount"])
    s += tabs + "message: {}\n".format(tx["contents"]["message"])
    s += tabs + "nonce: {}\n".format(tx["contents"]["nonce"])
    return s

def read_transaction_file(node_id):
    receivers = []
    messages = []
    with open(f"input/trans{node_id}.txt", 'r') as file:
        lines = file.readlines()

        for line in lines:
            receivers.append(int(line[2:line.find(" ")]))
            messages.append(line[line.find(" ") + 1:])

    return receivers, messages

