from helper import myIP


class Constants:
    BOOTSTRAP_IP_ADDRESS = myIP()
    BOOTSTRAP_PORT = 5000
    BOOTSTRAP_ID = 0
    BOOTSTRAP_PUBLIC_KEY = "dummy key"  # TODO: Define boostrap public key. It should not be generated on runtime.
    MAX_NODES = 2
    JSON_HEADER = {'Content-Type': 'application/json'}
    CAPACITY = 5
    STARTING_BCC_PER_NODE = 1000
    BOOTSTRAP_URL = f"http://{BOOTSTRAP_IP_ADDRESS}:{BOOTSTRAP_PORT}"

