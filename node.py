import logging

import requests

from constants import Constants
from helper import JSONSerializable
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder


class NodeInfo(JSONSerializable):
    def __init__(self, ip_address, port, public_key=None):
        self.ip_address = ip_address
        self.port = port
        self.public_key = public_key

    def get_node_url(self):
        url = f"{self.ip_address}:{self.port}"
        return url


class Node(NodeInfo):
    def __init__(self, ip_address, port, node_id=None):
        self.wallet = Wallet()
        self.other_nodes = {}
        self.tx_builder = TransactionBuilder(self.wallet)
        super().__init__(ip_address, port, self.wallet.public_key)
        if node_id is None:
            self.join_network()
        else:
            self.id = node_id

    def join_network(self):
        """
        Makes a request to the boostrap node in order to join the network.
        If the join is successful, the node is assigned an id.
        """

        logging.info("Sending request to Boostrap Node to join the network.")

        # Make request to boostrap node
        request = JoinRequest(self.public_key, self.ip_address, self.port)

        raw_response = requests.post(Constants.get_bootstrap_node_url() + "/nodes",
                                     json=request.to_dict(),
                                     headers=Constants.JSON_HEADER)
        response = JoinResponse.from_json(raw_response.json())

        # Assign returned id to node
        self.id = response.id

        logging.info(f"Joined the network successfully with id {self.id}.")


class Bootstrap(Node):
    def __init__(self):
        super().__init__(Constants.BOOTSTRAP_IP_ADDRESS,
                         Constants.BOOTSTRAP_PORT,
                         Constants.BOOTSTRAP_ID)

    def add_node(self, request: JoinRequest, id: int):
        self.other_nodes[id] = NodeInfo(request.ip_address, request.port, request.public_key)

    def node_has_joined(self, ip_address, port):
        for node in self.other_nodes.values():
            if node.ip_address == ip_address and node.port == port:
                return True
        return False
