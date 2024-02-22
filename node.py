import requests

from constants import Constants
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder

class NodeInfo:
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.public_key = None

class Node(NodeInfo):
    def __init__(self, ip_address, port, node_id=None):
        super().__init__(ip_address, port)
        self.id = node_id
        self.other_nodes = {}
        self.wallet = Wallet()
        self.public_key = self.wallet.public_key
        self.tx_builder = TransactionBuilder(self.wallet)

    def join_network(self):
        """
        Makes a request to the boostrap node in order to join the network.
        If the join is successful, the node is assigned an id.
        """

        # Make request to boostrap node
        request = JoinRequest(self.public_key, self.ip_address, self.port)

        raw_response = requests.post(Constants.get_bootstrap_node_url() + "/nodes",
                                     json=request.to_dict(),
                                     headers=Constants.JSON_HEADER)
        response = JoinResponse.from_json(raw_response.json())

        # Assign returned id to node
        self.id = response.id

class Bootstrap(Node):
    def __init__(self):
        super().__init__(Constants.BOOTSTRAP_IP_ADDRESS,
                         Constants.BOOTSTRAP_PORT,
                         Constants.BOOTSTRAP_ID)

    def add_node(self, request: JoinRequest, id: int):
        self.other_nodes[id] = (request.ip_address, request.port, request.public_key)

    def node_has_joined(self, ip_address, port):
        for node_ip, node_port, _ in self.other_nodes.values():
            if node_ip == ip_address and node_port == port:
                return True
        return False