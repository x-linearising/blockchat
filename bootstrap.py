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
        self.my_info = NodeInfo(
            Constants.BOOTSTRAP_IP_ADDRESS,
            Constants.BOOTSTRAP_PORT,
            self.public_key
        )
        self.all_nodes[self.id] = self.my_info
        self.genesis()

    def genesis(self):
        genesis_tx = self.tx_builder.create(
            Constants.BOOTSTRAP_PUBKEY,
            TransactionType.AMOUNT.value,
            Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES
        )

        genesis_block = Block(0, time(), [genesis_tx], self.my_info.public_key, 1)
        genesis_block.set_hash()
        
        self.blockchain.add(genesis_block)
        self.my_info.bcc = Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES
        self.val_bcc[self.id] = Constants.STARTING_BCC_PER_NODE * Constants.MAX_NODES
        self.expected_nonce[self.id] = 1
        self.validated_nonce[self.id] = 1

        print("Bootstrap bcc: {}".format(self.my_info.bcc))


    def node_has_joined(self, ip_address, port):
        for node in self.all_nodes.values():
            if node.ip_address == ip_address and node.port == port:
                return True
        return False

    def broadcast_node_list(self):
        # Send list to each node
        node_list_request = NodeListRequest.from_node_info_dict_to_request(self.all_nodes)
        self.broadcast_request(node_list_request, "/nodes")

        logging.info("Bootstrap phase complete. All nodes have received the participant list.")

    def broadcast_blockchain(self):
        req = BlockchainRequest.from_blockchain_to_request(self.blockchain)
        self.broadcast_request(req, "/blockchain")

        logging.info("Bootstrap phase complete. All nodes have received the blockchain.")

    def perform_initial_transactions(self):
        """
        Performed at the end of bootstrapping phase. Transfers the starting BCC amount to each node of the network.
        """

        for node_id, node in self.all_nodes.items():
            if node_id == Constants.BOOTSTRAP_ID:
                continue
            
            # print("Sending initial bcc to {}".format(node_id))
            transfer_amount = Constants.STARTING_BCC_PER_NODE
            print(f"Transfer amount : {transfer_amount}")
            tx = self.tx_builder.create(recv_addr=node.public_key,
                                        trans_type=TransactionType.AMOUNT.value,
                                        payload=transfer_amount)
            self.transactions.append(tx)
            node.bcc += transfer_amount
            self.my_info.bcc -= transfer_amount * Constants.TRANSFER_FEE_MULTIPLIER
            self.expected_nonce[self.id] += 1
            print("Bootstrap bcc: {}".format(self.my_info.bcc))
            self.broadcast_request(tx, "/transactions")



