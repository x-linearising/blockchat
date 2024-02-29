import logging
from time import time
from block import Block
from constants import Constants
from node import Node, NodeInfo
from request_classes.join_request import JoinRequest
from request_classes.node_list_request import NodeListRequest
from request_classes.blockchain_request import BlockchainRequest
from transaction import TransactionType


class Bootstrap(Node):
    def __init__(self):
        super().__init__(Constants.BOOTSTRAP_IP_ADDRESS,
                         Constants.BOOTSTRAP_PORT,
                         Constants.BOOTSTRAP_ID,
                         Constants.BOOTSTRAP_PRIVKEY_PATH)
        self.other_nodes[self.id] = NodeInfo(self.ip_address,
                                             self.port,
                                             self.public_key,
                                             self.bcc)
        self.genesis()

    def genesis(self):
        genesis_tx = self.tx_builder.create(
            Constants.BOOTSTRAP_PUBKEY,
            TransactionType.AMOUNT.value,
            Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES    
        )

        genesis_block = Block(0, time(), [genesis_tx], self.public_key, 1)
        genesis_block.set_hash()
        
        self.blockchain.add(genesis_block)
        self.other_nodes[self.id].bcc = Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES


    def node_has_joined(self, ip_address, port):
        for node in self.other_nodes.values():
            if node.ip_address == Constants.BOOTSTRAP_IP_ADDRESS and node.port == Constants.BOOTSTRAP_PORT:
                continue
            if node.ip_address == ip_address and node.port == port:
                return True
        return False

    def broadcast_node_list(self):
        # Adds itself to the list
        # complete_list = self.other_nodes.copy()
        # complete_list[self.id] = NodeInfo(self.ip_address,
        #                                   self.port,
        #                                   self.public_key,
        #                                   self.bcc)
        # Send list to each node
        node_list_request = NodeListRequest.from_node_info_dict_to_request(self.other_nodes)
        self.broadcast_request(node_list_request, "/nodes")

        for k in self.other_nodes.keys():
            self.expected_nonce[k] = 0

        logging.info("Bootstrap phase complete. All nodes have received the participant list.")

    def broadcast_blockchain(self):
        req = BlockchainRequest.from_blockchain_to_request(self.blockchain)
        self.broadcast_request(req, "/blockchain")

        logging.info("Bootstrap phase complete. All nodes have received the blockchain.")

    def perform_initial_transactions(self):
        """
        Performed at the end of bootstrapping phase. Transfers the starting BCC amount to each node of the network.
        """

        for node_id, node in self.other_nodes.items():
            if node_id == Constants.BOOTSTRAP_ID:
                continue
            transfer_amount = Constants.STARTING_BCC_PER_NODE
            tx = self.tx_builder.create(recv_addr=node.public_key,
                                        trans_type=TransactionType.AMOUNT.value,
                                        payload=transfer_amount)
            self.transactions.append(tx)
            self.broadcast_request(tx, "/transactions")
            node.bcc += transfer_amount
            self.other_nodes[Constants.BOOTSTRAP_ID].bcc -= transfer_amount * Constants.TRANSFER_FEE_MULTIPLIER


