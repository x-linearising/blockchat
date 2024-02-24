import logging
import requests
from threading import Thread
from time import sleep
from flask import Blueprint, abort, request

from node import NodeInfo, Node
from bootstrap import Bootstrap
from request_classes.blockchain_request import BlockchainRequest
from request_classes.node_list_request import NodeListRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from constants import Constants 


class NodeController:
    
    def __init__(self, ip_address, port):
        self.blueprint = Blueprint("nodes", __name__)
        # self.blockchain_blueprint = Blueprint("blockchain", __name__)
        # equivalent to using @self.blueprint.route on add_node
        # (which wouldn't work because of the self prefix)
        self.blueprint.add_url_rule("/nodes", "nodes", self.set_final_node_list, methods=["POST"])
        self.blueprint.add_url_rule("/blockchain", "blockchain", self.set_initial_blockchain, methods=["POST"])
        self.node = Node(ip_address, port)

    def set_final_node_list(self):
        """
        Endpoint hit by the bootstrap node, who sends the final list of nodes to all participating nodes.
        """
        logging.info(f"Received NodeInfo for {len(request.json)} nodes.")

        # Mapping request body to class
        nodes_info = NodeListRequest.from_request_to_node_info_dict(request.json)

        # Removes itself from the list.
        del nodes_info[self.node.id]

        # Updating node list
        self.node.other_nodes = nodes_info
        logging.info("Node list has been updated successfully.")

        # No need for response body. Responding with status 200.
        return '', 200

    def set_initial_blockchain(self):
        """
        Endpoint hit by the bootstrap node, who sends the blockchain after bootstrap phase is complete.
        """

        logging.info(f"Received initial state of blockchain.")

        # Mapping request body to class
        blocks = BlockchainRequest.from_request_to_blocks(request.json)

        # Updating node list
        self.node.blockchain.blocks = blocks
        logging.info("Blockchain has been updated successfully.")

        # No need for response body. Responding with status 200.
        return '', 200


class BootstrapController(NodeController):

    def __init__(self):
        self.node = Bootstrap()
        self.blueprint = Blueprint("nodes", __name__)
        self.nodes_counter = 1
        self.is_bootstrapping_phase_over = False
        # equivalent to using @self.blueprint.route on add_node
        # (which wouldn't work because of the self prefix)
        self.blueprint.add_url_rule("/nodes", "nodes", self.add_node, methods=["POST"])
        t = Thread(target=self.poll_node_count)
        t.start()

    def poll_node_count(self):
        while True:
            if self.is_bootstrapping_phase_over:
                print("[Poll Thread] Bootstrap phase over. Broadcasting...")
                self.node.broadcast_node_list()
                self.node.broadcast_blockchain()
                return
            else:
                sleep(1)

    def add_node(self):
        """
        Method that gets called when a node sends a POST request at the /nodes endpoint
        Adds the node's info (public key, ip, port) to the bootstraps node list and
        returns the node's assigned id.
        """

        # Mapping request body to class

        join_request = JoinRequest.from_json(request.json)
        logging.info("Received request to add the following node to the network: {}:{}"
            .format(request.json["ip_address"], request.json["port"]))

        # Performing validations
        self.validate_join_request(join_request)

        # Adding node
        self.node.add_node(join_request, self.nodes_counter)
        logging.info(f"Node with id {self.nodes_counter} has been added to the network.")

        # Creating response
        response = JoinResponse(self.nodes_counter)
        self.nodes_counter += 1

        # Check if every expected node has joined
        if self.nodes_counter == Constants.MAX_NODES:
            self.is_bootstrapping_phase_over = True
            print("<i should broadcast now>")

        return response.to_dict()

    def validate_join_request(self, join_request: JoinRequest):
        if self.is_bootstrapping_phase_over:
            log_message = "Bad request: Bootstrapping phase is over."
            logging.warning(log_message)
            abort(400, description=log_message)

        if self.node.node_has_joined(join_request.ip_address, join_request.port):
            log_message = "Bad request: Node with given ip and port has already been added."
            logging.warning(log_message)
            abort(400, description=log_message)
