import logging

from constants import Constants
from node import Node, NodeInfo
from request_classes.join_request import JoinRequest
from request_classes.node_list_request import NodeListRequest


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

    def broadcast_node_list(self):
        # Adds itself to the list
        complete_list = self.other_nodes.copy()  # TODO: Check if this is deep copy.
        complete_list[self.id] = NodeInfo(self.ip_address,
                                          self.port,
                                          self.public_key)

        # Send list to each node
        node_list_request = NodeListRequest.from_node_info_dict_to_request(complete_list)
        self.broadcast_request(node_list_request, "/nodes")

        logging.info("Bootstrap phase complete. All nodes have received the participant list.")
