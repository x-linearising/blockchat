import json
import logging
from threading import Thread
from time import sleep
from flask import Blueprint, abort, request

from node import Node, NodeInfo
from bootstrap import Bootstrap
from helper import tx_str
from request_classes.block_request import BlockRequest
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
        self.blueprint.add_url_rule("/blocks", "blocks", self.receive_block, methods=["POST"])
        self.node = Node(ip_address, port)
        t2 = Thread(target=self.poll_capacity)
        t2.start()

    def receive_transaction(self):
        """
        Endpoint hit by a node broadcasting a transaction.
        """

        # Extracting information from request
        transaction_as_dict = request.json
        tx_contents = transaction_as_dict["contents"]
        sender_public_key = tx_contents["sender_addr"]
        sender_info = self.node.get_node_info_by_public_key(sender_public_key)
        sender_id = self.node.get_node_id_by_public_key(sender_public_key)

        # logging.info(f"Received transaction from Node {sender_id}.")

        # Transaction Cost
        match tx_contents["type"]:
            case TransactionType.MESSAGE.value:
                transaction_cost = len(tx_contents["message"])
            case TransactionType.AMOUNT.value:
                transaction_cost = tx_contents["amount"] * Constants.TRANSFER_FEE_MULTIPLIER
            case TransactionType.STAKE.value:
                transaction_cost = tx_contents["amount"] - self.node.stakes[sender_id]  # This could be very well be negative
            case _:
                logging.warning("Invalid transaction type was detected.")
                return "Invalid transaction type", 400

        # Transaction validations
        if not verify_tx(transaction_as_dict, self.node.expected_nonce[sender_id]):
            return "Invalid signature.", 400
        if transaction_cost > sender_info.bcc:   # Stakes are not contained in bcc attribute.
            logging.warning("Transaction is not valid as node's amount is not sufficient.")
            return "Not enough bcc to carry out transaction.", 400

        # We assume that we cannot receive out-of-order transactions from the same sender,
        # since senders wait for ACKs before continuing.
        # Therefore the scenario of receiving the message w/ nonce n after n+1 is
        # impossible 
        self.node.expected_nonce[sender_id] += 1
        # BCCs and transaction list updates
        sender_info.bcc -= transaction_cost
        if tx_contents["type"] == TransactionType.STAKE.value:
            self.node.stakes[sender_id] = tx_contents["amount"]
        if tx_contents["type"] == TransactionType.AMOUNT.value:
            self.node.get_node_info_by_public_key(tx_contents["recv_addr"]).bcc += tx_contents["amount"]

            if tx_contents["recv_addr"] == self.node.public_key:
                logging.info("I received {} BCC".format(tx_contents["amount"]))

        self.node.transactions.append(transaction_as_dict)

        return '', 200

    def set_final_node_list(self):
        """
        Endpoint hit by the bootstrap node, who sends the final list of nodes to all participating nodes.
        """
        logging.info(f"Received NodeInfo for {len(request.json)} nodes.")

        # Mapping request body to class
        nodes_info = NodeListRequest.from_request_to_node_info_dict(request.json)

        # Removes itself from the list.
        # del nodes_info[self.node.id]

        # Updating node list
        self.node.other_nodes = nodes_info
        logging.info("Node list has been updated successfully.")

        # Initialize stakes at predefined value
        self.node.initialize_stakes()

        for k in nodes_info.keys():
            self.node.expected_nonce[k] = 0

        # No need for response body. Responding with status 200.
        return '', 200

    def set_initial_blockchain(self):
        """
        Endpoint hit by the bootstrap node, who sends the blockchain after bootstrap phase is complete.
        """

        logging.info(f"Received initial state of blockchain:")

        # Mapping request body to class
        blocks = BlockchainRequest.from_request_to_blocks(request.json)
        # print(blocks[0].to_str())

        # Updating node list
        self.node.blockchain.blocks = blocks
        
        logging.info("Blockchain has been updated successfully.")

        self.node.is_validator = (self.node.public_key == self.node.next_validator())

        # No need for response body. Responding with status 200.
        return '', 200

    def poll_capacity(self):
        while True:
            if self.node.is_validator and len(self.node.transactions) >= Constants.CAPACITY:
                print("Validator sends a block.")
                self.node.mint_block()
            else:
                sleep(1)

    def receive_block(self):
        b = BlockRequest.from_request_to_block(request.json)

        print("Received block!")

        if not b.validate(b.validator, b.prev_hash):
            return " ", 400

        val_id = self.node.get_node_id_by_public_key(b.validator)
        print("Giving {:.2f} to the validator".format(b.fees()))
        self.node.other_nodes[val_id].bcc += b.fees()

        self.node.blockchain.add(b)
        self.node.transactions = self.node.transactions[Constants.CAPACITY:]

        for staker_public_key, stake in b.stakes().items():
            self.node.validated_stakes[self.node.get_node_id_by_public_key(staker_public_key)] = stake
            
        next_validator = self.node.next_validator()
        self.node.is_validator = next_validator == self.node.public_key 
        return "", 200


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
        self.blueprint.add_url_rule("/blocks", "blocks", self.receive_block, methods=["POST"])
        t = Thread(target=self.poll_node_count)
        t.start()
        t2 = Thread(target=self.poll_capacity)
        t2.start()

    def poll_node_count(self):
        while True:
            if self.is_bootstrapping_phase_over:
                print("[Poll Thread] Bootstrap phase over. Broadcasting...")
                self.node.broadcast_node_list()
                self.node.broadcast_blockchain()
                self.node.initialize_stakes()
                next_validator = self.node.next_validator()
                self.node.is_validator = next_validator == self.node.public_key 
                self.node.perform_initial_transactions()
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
        self.node.other_nodes[self.nodes_counter] = NodeInfo(
            join_request.ip_address,
            join_request.port,
            join_request.public_key
        )
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
