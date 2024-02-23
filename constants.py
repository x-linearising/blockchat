from helper import myIP


class Constants:
    BOOTSTRAP_IP_ADDRESS = myIP()
    BOOTSTRAP_PORT = 5000
    BOOTSTRAP_ID = 0
    BOOTSTRAP_PUBLIC_KEY = "dummy key"  # TODO: Define boostrap public key. It should not be generated on runtime.
    MAX_NODES = 3
    JSON_HEADER = {'Content-Type': 'application/json'}
    CAPACITY = 5

    @classmethod
    def get_bootstrap_node_url(cls):
        url = f"http://{cls.BOOTSTRAP_IP_ADDRESS}:{cls.BOOTSTRAP_PORT}"
        return url

