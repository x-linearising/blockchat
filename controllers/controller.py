import json
import logging
from threading import Thread
from time import sleep
from flask import Blueprint, abort, request

from node import Node
from bootstrap import Bootstrap
from request_classes.blockchain_request import BlockchainRequest
from request_classes.node_list_request import NodeListRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from constants import Constants
from transaction import verify_tx, TransactionType


class NodeController:
    
    def __init__(self, ip_address, port):
        self.blueprint = Blueprint("bootstrap blueprint", __name__)
        # equivalent to using @self.blueprint.route on add_node
        # (which wouldn't work because of the self prefix)
        self.blueprint.add_url_rule("/nodes", "nodes", self.set_final_node_list, methods=["POST"])
        self.blueprint.add_url_rule("/blockchain", "blockchain", self.set_initial_blockchain, methods=["POST"])
        self.blueprint.add_url_rule("/transactions", "transaction", self.receive_transaction, methods=["POST"])
        self.node = Node(ip_address, port)

    def receive_transaction(self):
        """
        Endpoint hit by a node broadcasting a transaction.
        """

        # Extracting information from request
        transaction_as_string = request.json
        transaction_as_dict = json.loads(transaction_as_string)
        tx_contents = json.loads(transaction_as_dict["contents"])
        sender_public_key = tx_contents["sender_addr"]
        sender_info = self.node.get_node_info_by_public_key(sender_public_key)

        logging.info(f"Received transaction from Node {self.node.get_node_id_by_public_key(sender_public_key)}.")

        # Transaction Cost
        if tx_contents["type"] == TransactionType.MESSAGE.value:
            transaction_cost = len(tx_contents["message"])
        else:
            transaction_cost = tx_contents["amount"] * Constants.TRANSFER_FEE_MULTIPLIER

        # Transaction validations
        if not verify_tx(transaction_as_string):
            return "Invalid signature.", 400
        if transaction_cost > sender_info.bcc:   # Stakes are not contained in bcc attribute.
            logging.warning("Transaction is not valid as node's amount is not sufficient.")
            return "Not enough bcc to carry out transaction.", 400

        # BCCs and transaction list updates
        sender_info.bcc -= transaction_cost
        if tx_contents["type"] == TransactionType.AMOUNT.value:
            if tx_contents["recv_addr"] == self.node.public_key:
                self.node.bcc += tx_contents["amount"]
                logging.info(f"Node's BCCs have increased to [{self.node.bcc}].")
            else:
                recv_id = self.node.get_node_id_by_public_key(tx_contents["recv_addr"])
                self.node.other_nodes[recv_id].bcc += tx_contents["amount"]
                logging.info(f"BCCs of node {recv_id} have increased to [{self.node.other_nodes[recv_id].bcc}].")

        self.node.transactions.append(transaction_as_dict)
        # TODO: Check if capacity reached on separate thread.
        logging.warning("Capacity checks have not been implemented yet!")

        return '', 200

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

        # TODO: Remove this after adding blockchain validation? BCCs can be calculated from there.
        for node_info in self.node.other_nodes.values():
            node_info.bcc = Constants.STARTING_BCC_PER_NODE
        self.node.bcc = Constants.STARTING_BCC_PER_NODE

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
        self.blueprint.add_url_rule("/transactions", "transactions", self.receive_transaction, methods=["POST"])
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
