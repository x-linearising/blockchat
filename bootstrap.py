import logging
from time import time
from block import Block
from constants import Constants
from node import Node, NodeInfo
from request_classes.join_request import JoinRequest
from request_classes.node_list_request import NodeListRequest
from transaction import TransactionType


class Bootstrap(Node):
    def __init__(self):
        super().__init__(Constants.BOOTSTRAP_IP_ADDRESS,
                         Constants.BOOTSTRAP_PORT,
                         Constants.BOOTSTRAP_ID)
        self.genesis()

    def genesis(self):
        genesis_tx = self.tx_builder.create(
            Constants.BOOTSTRAP_PUBLIC_KEY,
            TransactionType.AMOUNT.value,
            Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES    
        )

        genesis_block = Block(0, time(), [genesis_tx], self.public_key, 1)
        genesis_block.block_hash = genesis_block.hash()
        
        self.blockchain.add(genesis_block)
        self.bcc = Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES

    def add_node(self, request: JoinRequest, id: int):
        self.other_nodes[id] = NodeInfo(request.ip_address, request.port, request.public_key)
        tx = self.tx_builder.create(recv_addr=self.public_key,
                                    trans_type=TransactionType.AMOUNT.value,
                                    payload=Constants.STARTING_BCC_PER_NODE)
        self.transactions.append(tx)
        self.other_nodes[id].bcc = Constants.STARTING_BCC_PER_NODE
        self.bcc -= Constants.STARTING_BCC_PER_NODE


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

    def broadcast_blockchain(self):
        blockchain_request = BlockchainRequest.from_blockchain_to_request(self.node.blockchain)
        for node_id, node in self.node.other_nodes.items():
            response = requests.post(node.get_node_url() + "/blockchain",
                                     json=blockchain_request,
                                     headers=Constants.JSON_HEADER)
            if response.ok:
                logging.info(f"Request to node {node_id} was successful with status code: {response.status_code}.")
            else:
                logging.error(f"Request to node {node_id} failed with status code: {response.status_code}.")

        logging.info("Bootstrap phase complete. All nodes have received the blockchain.")