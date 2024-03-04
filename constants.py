from os import path
from helper import myIP, read_pubkey

class Constants:
    BOOTSTRAP_IP_ADDRESS = myIP()
    BOOTSTRAP_PORT = 5000
    BOOTSTRAP_ID = 0
    BOOTSTRAP_PUBKEY_PATH = path.join(".", "bootstrap_keys", "id_rsa.pub")
    BOOTSTRAP_PUBKEY = read_pubkey(BOOTSTRAP_PUBKEY_PATH)
    BOOTSTRAP_PRIVKEY_PATH = path.join(".", "bootstrap_keys", "id_rsa")
    BOOTSTRAP_URL = f"http://{BOOTSTRAP_IP_ADDRESS}:{BOOTSTRAP_PORT}"

    MAX_NODES = 3
    JSON_HEADER = {'Content-Type': 'application/json'}
    CAPACITY = 5
    STARTING_BCC_PER_NODE = 1000
    TRANSFER_FEE_MULTIPLIER = 1.03
    INITIAL_STAKE = 50

