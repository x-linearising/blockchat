import os
from helper import myIP, read_pubkey

class Constants:
    SRC_PATH = os.path.dirname(os.path.abspath(__file__))

    BOOTSTRAP_IP_ADDRESS = "127.0.0.1"
    BOOTSTRAP_PORT = 5000
    BOOTSTRAP_ID = 0
    BOOTSTRAP_PUBKEY_PATH = os.path.join(SRC_PATH, "bootstrap_keys", "id_rsa.pub")
    BOOTSTRAP_PUBKEY = read_pubkey(BOOTSTRAP_PUBKEY_PATH)
    BOOTSTRAP_PRIVKEY_PATH = os.path.join(SRC_PATH, "bootstrap_keys", "id_rsa")

    MAX_NODES = 5
    JSON_HEADER = {'Content-Type': 'application/json'}
    CAPACITY = 20
    STARTING_BCC_PER_NODE = 1000
    TRANSFER_FEE_MULTIPLIER = 1.03
    INITIAL_STAKE = 10

