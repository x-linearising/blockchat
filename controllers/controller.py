import logging
from flask import Blueprint, abort, request

from node import Node, NodeInfo
from bootstrap import Bootstrap
from request_classes.block_request import BlockRequest
from request_classes.blockchain_request import BlockchainRequest
from request_classes.node_list_request import NodeListRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from constants import Constants
from transaction import TransactionType, verify_tx, tx_cost 


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

    def after_request(self, response):
        request_path = request.path

        @response.call_on_close
        def process_after_request():
            if request_path == '/nodes':
                print("[Poll Thread] Bootstrap phase over. Executing file transactions...")
                self.node.execute_file_transactions()
            elif request_path == '/transactions':
                if self.node.is_validator and len(self.node.transactions) >= Constants.CAPACITY:
                    print("Validator sends a block.")
                    self.node.mint_block()
        return response


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
        
        recv_public_key = tx_contents["recv_addr"]
        recv_info = self.node.get_node_info_by_public_key(recv_public_key)
        recv_id = self.node.get_node_id_by_public_key(recv_public_key)

        # logging.info(f"Received transaction from Node {sender_id}.")

        # Transaction Cost
        transaction_cost = tx_cost(tx_contents, self.node.stakes[sender_id])
        if transaction_cost is None:
            logging.warning("Invalid transaction type was detected.")

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
            recv_info.bcc += tx_contents["amount"]

            if recv_public_key == self.node.public_key:
                print(f"My id: {self.node.id} Recv ID: {recv_id} My bcc: {self.node.my_info.bcc}")
                logging.info("I received {} BCC".format(tx_contents["amount"]))

        if transaction_as_dict["hash"] not in self.node.pending_tx:
            self.node.transactions.append(transaction_as_dict)


        return '', 200

    def set_final_node_list(self):
        """
        Endpoint hit by the bootstrap node, who sends the final list of nodes to all participating nodes.
        """

        # Updating node list
        self.node.all_nodes = NodeListRequest.from_request_to_node_info_dict(request.json)
        self.node.val_bcc = {node_id: node_info.bcc for node_id, node_info in self.node.all_nodes.items()}
        self.node.my_info = self.node.all_nodes[self.node.id]
        logging.info(f"[Bootstrap Phase] Received NodeInfo for {len(request.json)} nodes.")

        # Initialize stakes at predefined value
        self.node.initialize_stakes()

        for k in self.node.all_nodes.keys():
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

    def receive_block(self):
        b = BlockRequest.from_request_to_block(request.json)

        print("Received block!")

        if not b.validate(b.validator, b.prev_hash):
            return " ", 400

        val_id = self.node.get_node_id_by_public_key(b.validator)
        print("Giving {:.2f} to the validator".format(b.fees()))
        self.node.all_nodes[val_id].bcc += b.fees()
        self.node.blockchain.add(b)

        # If the block contains a tx that this node hasn't received, add its
        # hash to the pending_tx list.
        for tx in [i for i in b.transactions if i not in self.node.transactions]:
            self.node.pending_tx.append(tx['hash'])
        
        # Remove txs included in the block from this node's list
        self.node.transactions = [i for i in self.node.transactions if i not in b.transactions]

        # validated BCCs
        for tx in b.transactions:
            sender_pubkey = tx["contents"]["sender_addr"]
            sender_id = self.node.get_node_id_by_public_key(sender_pubkey)
            self.node.val_bcc[sender_id] -= tx_cost(tx['contents'], self.node.validated_stakes[sender_id])
            if tx["contents"]["type"] == TransactionType.STAKE.value:
                self.node.validated_stakes[sender_id] = tx["contents"]["amount"]
            if tx["contents"]["type"] == TransactionType.AMOUNT.value:
                recv_pubkey = tx["contents"]["recv_addr"]
                recv_id = self.node.get_node_id_by_public_key(recv_pubkey)
                self.node.val_bcc[recv_id] += tx["contents"]["amount"]
        
        self.node.val_bcc[val_id] += b.fees()

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


    def after_request(self, response):
        request_path = request.path

        @response.call_on_close
        def process_after_request():
            if request_path == '/nodes' and self.nodes_counter == Constants.MAX_NODES:
                print("[Poll Thread] Bootstrap phase over. Broadcasting...")
                self.node.broadcast_node_list()
                self.node.broadcast_blockchain()
                self.node.initialize_stakes()
                next_validator = self.node.next_validator()
                self.node.is_validator = next_validator == self.node.public_key
                self.node.perform_initial_transactions()
                self.node.execute_file_transactions()

        return response


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
        self.node.all_nodes[self.nodes_counter] = NodeInfo(
            join_request.ip_address,
            join_request.port,
            join_request.public_key
        )
        logging.info(f"Node with id {self.nodes_counter} has been added to the network.")

        # Creating response
        response = JoinResponse(self.nodes_counter)
        self.nodes_counter += 1

        return response.to_dict()

    def validate_join_request(self, join_request: JoinRequest):
        if self.nodes_counter == Constants.MAX_NODES:
            log_message = "Bad request: Bootstrapping phase is over."
            logging.warning(log_message)
            abort(400, description=log_message)

        if self.node.node_has_joined(join_request.ip_address, join_request.port):
            log_message = "Bad request: Node with given ip and port has already been added."
            logging.warning(log_message)
            abort(400, description=log_message)
