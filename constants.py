class Constants:
    BOOTSTRAP_IP_ADDRESS = "http://localhost"
    BOOTSTRAP_PORT = 5000
    BOOTSTRAP_ID = 0
    BOOTSTRAP_PUBLIC_KEY = "dummy key"  # TODO: Define boostrap public key. It should not be generated on runtime.

    @classmethod
    def get_bootstrap_node_url(cls):
        url = f"{cls.BOOTSTRAP_IP_ADDRESS}:{cls.BOOTSTRAP_PORT}"
        return url

