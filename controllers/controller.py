import logging
from threading import Lock
from flask import Blueprint, request

from helper import BootstrapConnError
from node import Node, NodeInfo
from bootstrap import Bootstrap
from request_classes.block_request import BlockRequest
from request_classes.blockchain_request import BlockchainRequest
from request_classes.node_list_request import NodeListRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from constants import Constants
from transaction import TransactionType, verify_tx, tx_cost 

recv_tx = 0

class NodeController:
    
    def __init__(self, ip_address, port):
        self.blueprint = Blueprint("bootstrap blueprint", __name__)
        # equivalent to using @self.blueprint.route on add_node
        # (which wouldn't work because of the self prefix)
        self.blueprint.add_url_rule("/nodes", "nodes", self.set_final_node_list, methods=["POST"])
        self.blueprint.add_url_rule("/blockchain", "blockchain", self.set_initial_blockchain, methods=["POST"])
        self.blueprint.add_url_rule("/transactions", "transaction", self.receive_transaction, methods=["POST"])
        self.blueprint.add_url_rule("/blocks", "blocks", self.receive_block, methods=["POST"])
        try:
            self.node = Node(ip_address, port)
        except BootstrapConnError as e:
            raise BootstrapConnError(e.msg)

    def after_request(self, response):
        request_path = request.path

        @response.call_on_close
        def process_after_request():
            global recv_tx
            if request_path == '/blockchain':
                pass
            elif request_path == '/transactions':
                recv_tx += 1
                if recv_tx == Constants.MAX_NODES - 1:
                    print("Received initial BCCs, BROADCASTING FILE TXs")
                    self.node.execute_file_transactions()

        return response


    def process_soft_tx(self, tx, soft=True):
        tx_contents = tx["contents"]

        sender_public_key = tx_contents["sender_addr"]
        sender_info = self.node.get_node_info_by_public_key(sender_public_key)
        sender_id = self.node.get_node_id_by_public_key(sender_public_key)
        
        recv_public_key = tx_contents["recv_addr"]
        recv_info = self.node.get_node_info_by_public_key(recv_public_key)
        recv_id = self.node.get_node_id_by_public_key(recv_public_key)
        
        transaction_cost = tx_cost(tx_contents, self.node.soft_stakes[sender_id])
        if transaction_cost is None:
            err = "Invalid transaction type was detected."
            logging.warning(err)
            return False, err

        # Transaction validations
        if not verify_tx(tx, self.node.soft_nonce[sender_id]):
            return False, "[SOFT] Invalid signature."
        if transaction_cost > sender_info.bcc:   # Stakes are not contained in bcc attribute.
            return False, "[SOFT] Not enough bcc to carry out transaction."

        # We assume that we cannot receive out-of-order transactions from the same sender,
        # since senders wait for ACKs before continuing.
        # Therefore the scenario of receiving the message w/ nonce n after n+1 is
        # impossible 
        self.node.soft_nonce[sender_id] += 1

        # BCCs and transaction list updates
        sender_info.bcc -= transaction_cost

        if tx_contents["type"] == TransactionType.STAKE.value:
            self.node.soft_stakes[sender_id] = tx_contents["amount"]
        elif tx_contents["type"] == TransactionType.AMOUNT.value:
            recv_info.bcc += tx_contents["amount"]

        return True, ""


    def process_hard_tx(self, tx):
        tx_contents = tx["contents"]

        sender_public_key = tx_contents["sender_addr"]
        sender_id = self.node.get_node_id_by_public_key(sender_public_key)
        
        recv_public_key = tx_contents["recv_addr"]
        recv_id = self.node.get_node_id_by_public_key(recv_public_key)
        
        transaction_cost = tx_cost(tx_contents, self.node.hard_stakes[sender_id])
        if transaction_cost is None:
            err = "Invalid transaction type was detected."
            logging.warning(err)
            return False, err

        # Transaction validations
        if not verify_tx(tx, self.node.hard_nonce[sender_id]):
            return False, "[HARD] Invalid signature."
        if transaction_cost > self.node.hard_bcc[sender_id]:   # Stakes are not contained in bcc attribute.
            return False, "[HARD] Not enough bcc to carry out transaction."

        # if the validated transactions jump from nonce n-1 to n+1,
        # invalidate tx with nonce n in this node's soft TXs
        for i, node_tx in reversed(list(enumerate(self.node.transactions))):
            if node_tx["contents"]["sender_addr"] != tx["contents"]["sender_addr"]:
                continue
            if node_tx["contents"]["nonce"] < tx_contents["nonce"]:
                del self.node.transactions[i]

        self.node.hard_nonce[sender_id] = tx_contents["nonce"] + 1

        # BCCs and transaction list updates
        self.node.hard_bcc[sender_id] -= transaction_cost

        if tx_contents["type"] == TransactionType.STAKE.value:
            self.node.hard_stakes[sender_id] = tx_contents["amount"]
        elif tx_contents["type"] == TransactionType.AMOUNT.value:
            self.node.hard_bcc[recv_id] += tx_contents["amount"]

        return True, ""

    def receive_transaction(self):
        """
        Endpoint hit by a node broadcasting a transaction.
        """
        self.node.lock.acquire()
        tx = request.json
        valid, err = self.process_soft_tx(tx)
        if not valid:
            logging.warning(err)
            self.node.lock.release()
            return err, 400

        if tx["hash"] not in self.node.pending_tx:
            self.node.transactions.append(tx)
        else:
            self.node.pending_tx.remove(tx["hash"])

        self.node.lock.release()
        return '', 200

    def set_final_node_list(self):
        """
        Endpoint hit by the bootstrap node, who sends the final list of nodes to all participating nodes.
        """
        self.node.lock.acquire()
        
        # Received final node list. Soft and hard BCC are initialized to zero.
        self.node.all_nodes = NodeListRequest.from_request_to_node_info_dict(request.json)
        self.node.hard_bcc = {node_id: 0 for node_id in self.node.all_nodes.keys()}
        self.node.my_info = self.node.all_nodes[self.node.id]
        logging.info(f"[Bootstrap Phase] Received NodeInfo for {len(request.json)} nodes.")

        # Initialize stakes at predefined value
        self.node.initialize_stakes()

        for k in self.node.all_nodes.keys():
            if k == Constants.BOOTSTRAP_ID:
                self.node.soft_nonce[k] = 1
                self.node.hard_nonce[k] = 1
            else:
                self.node.soft_nonce[k] = 0
                self.node.hard_nonce[k] = 0

        self.node.lock.release()
        # No need for response body. Responding with status 200.
        return '', 200

    def set_initial_blockchain(self):
        """
        Endpoint hit by the bootstrap node, who sends the blockchain after bootstrap phase is complete.
        """
        self.node.lock.acquire()

        self.node.blockchain.blocks = BlockchainRequest.from_request_to_blocks(request.json)
        init_bcc = self.node.blockchain.blocks[0].transactions[0]["contents"]["amount"]
        # Initialize soft and hard states of bootstrap's bcc with the amount
        # given to it by the genesis transaction.
        self.node.all_nodes[Constants.BOOTSTRAP_ID].bcc += init_bcc
        self.node.hard_bcc[Constants.BOOTSTRAP_ID] += init_bcc

        logging.info("[Bootstrap Phase] Blockchain has been updated successfully.")
        self.node.lock.release()

        return '', 200

    def process_block(self, b):

        idx = b.idx - 1

        print("[PROCESS BLOCK with idx {} VAL = {} EXP_VAL = {}]".format(
            b.idx,
            b.validator[100:110],
            self.node.next_validator(idx)[100:110]
            ))
        
        if not b.validate(self.node.next_validator(idx), self.node.blockchain.blocks[idx].block_hash):
            return
        
        # Check that the block contains valid TXs
        for tx in b.transactions:
            valid, err = self.process_hard_tx(tx)
            if not valid:
                logging.warn(err)
                return


        val_id = self.node.get_node_id_by_public_key(b.validator)
        self.node.hard_bcc[val_id] += b.fees()
        
        # If the block contains a tx that this node hasn't received, add its
        # hash to the pending_tx list.
        block_tx_hashes = [tx["hash"] for tx in b.transactions]
        node_tx_hashes = [tx["hash"] for tx in self.node.transactions]

        for tx_hash in [i for i in block_tx_hashes if i not in node_tx_hashes]:
            self.node.pending_tx.add(tx_hash)

        # print("Block TX")
        # for i in b.transactions:
        #     print(i["hash"])
        # print("\nMy TX BEFORE")
        # for i in self.node.transactions:
        #     print(i["hash"])
        # print("\nDIFF")
        # for i in diff:
        #     print(i)

        # Remove txs included in the block from this node's list
        self.node.transactions = [i for i in self.node.transactions if i not in b.transactions]

        # Reset soft state to current hard state
        for k in self.node.hard_bcc.keys():
            self.node.all_nodes[k].bcc = self.node.hard_bcc[k]            
            self.node.soft_nonce[k] = self.node.hard_nonce[k]
            self.node.soft_stakes[k] = self.node.hard_stakes[k]

        # Re-apply received transactions to soft state
        for tx in self.node.transactions:
            valid, err = self.process_soft_tx(tx)
            if not valid:
                logging.warn(err)

        self.node.blockchain.add(b)

        # for i in range(Constants.MAX_NODES):
        #     print("{:<2d} {:<7.2f} {:<7.2f}".format(i, self.node.all_nodes[i].bcc, self.node.hard_bcc[i]))

        print(f"\n[PROCESS BLOCK with idx {b.idx} DONE]")


    def receive_block(self):
        """
        Called when this node receives a request at the "/blocks" endpoint.
        After checking that the block is valid, adds it to the blockchain
        and calculates the next expected validator.
        """
        self.node.lock.acquire()

        b = BlockRequest.from_request_to_block(request.json)
        self.node.pending_blocks[b.idx] = b
        expected_index = self.node.blockchain.blocks[-1].idx + 1
        while self.node.pending_blocks.get(expected_index) is not None:
            self.process_block(self.node.pending_blocks.pop(expected_index))
            expected_index += 1

        l = len(self.node.pending_blocks)

        if l > 0:
            print(f"[RECV BLOCK] have {l} pending blocks")

        self.node.lock.release()
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
        self.node.lock.acquire()
        request_path = request.path

        @response.call_on_close
        def process_after_request():
            if request_path == '/nodes' and self.nodes_counter == Constants.MAX_NODES:
                self.node.broadcast_node_list()
                self.node.broadcast_blockchain()
                self.node.initialize_stakes()
                self.node.perform_initial_transactions()
                self.node.execute_file_transactions()

        self.node.lock.release()
        return response


    def add_node(self):
        """
        Method that gets called when a node sends a POST request at the /nodes endpoint
        Adds the node's info (public key, ip, port) to the bootstraps node list and
        returns the node's assigned id.
        """
        self.node.lock.acquire()
        # Mapping request body to class

        join_request = JoinRequest.from_json(request.json)
        logging.info("Received request to add the following node to the network: {}:{}"
            .format(request.json["ip_address"], request.json["port"]))

        # Performing validations
        err = self.validate_join_request(join_request)
        if err:
            print(err)
            self.node.lock.release()
            return(err, 400)

        # Adding node
        self.node.all_nodes[self.nodes_counter] = NodeInfo(
            join_request.ip_address,
            join_request.port,
            join_request.public_key
        )
        self.node.hard_bcc[self.nodes_counter] = 0
        self.node.soft_nonce[self.nodes_counter] = 0
        self.node.hard_nonce[self.nodes_counter] = 0
        logging.info(f"Node with id {self.nodes_counter} has been added to the network.")

        # Creating response
        response = JoinResponse(self.nodes_counter)
        self.nodes_counter += 1

        self.node.lock.release()
        return response.to_dict()

    def validate_join_request(self, join_request: JoinRequest):
        err = None
        if self.nodes_counter == Constants.MAX_NODES:
            err = "Bad request: Bootstrapping phase is over."
        if self.node.node_has_joined(join_request.ip_address, join_request.port):
            err = "Bad request: Node with given ip and port has already been added."
        return err

