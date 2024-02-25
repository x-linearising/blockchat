import logging
import time

import requests

from block import Block
from blockchain import Blockchain
from constants import Constants
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder, TransactionType


class NodeInfo:
    def __init__(self, ip_address, port, public_key=None):
        self.ip_address = ip_address
        self.port = port
        self.public_key = public_key
        self.bcc = 0

    def get_node_url(self):
        url = f"http://{self.ip_address}:{self.port}"
        return url


class Node(NodeInfo):
    def __init__(self, ip_address, port, node_id=None):
        self.wallet = Wallet()
        self.other_nodes: dict[int, NodeInfo] = {}
        self.tx_builder = TransactionBuilder(self.wallet)
        super().__init__(ip_address, port, self.wallet.public_key)
        if node_id is None:
            self.join_network()  # TODO: Maybe move this in Controller?
        else:
            self.id = node_id
        
        self.transactions = []
        self.stakes = {}
        self.blockchain = Blockchain()

    def initialize_stakes(self):
        self.stakes[self.id] = Constants.INITIAL_STAKE
        self.bcc -= Constants.INITIAL_STAKE
        for node_id, node_info in self.other_nodes.items():
            self.stakes[node_id] = Constants.INITIAL_STAKE
            self.other_nodes[node_id].bcc -= Constants.INITIAL_STAKE
        return self.stakes

    def get_node_info_by_public_key(self, public_key):
        for node_info in self.other_nodes.values():
            if node_info.public_key == public_key:
                return node_info

    def get_node_id_by_public_key(self, public_key):
        for node_id, node_info in self.other_nodes.items():
            if node_info.public_key == public_key:
                return node_id

    def join_network(self):
        """
        Makes a request to the boostrap node in order to join the network.
        If the join is successful, the node is assigned an id.
        """

        logging.info("Sending request to Boostrap Node to join the network.")

        # Make request to boostrap node
        join_request = JoinRequest(self.public_key, self.ip_address, self.port)

        join_response = requests.post(Constants.BOOTSTRAP_URL + "/nodes",
                                      json=join_request.to_dict(),
                                      headers=Constants.JSON_HEADER)

        if join_response.ok:
            response = JoinResponse.from_json(join_response.json())
            self.id = response.id
            logging.info(f"Joined the network successfully with id {self.id}. Waiting for bootstrap phase completion.")
        else:
            logging.error(f"""Could not join the network. Bootstrap node responded 
                          with status [{join_response.status_code}] and message [{join_response.text}].""")

    def broadcast_request(self, request_body, endpoint):
        for node_id, node in self.other_nodes.items():
            response = requests.post(node.get_node_url() + endpoint,
                                     json=request_body,
                                     headers=Constants.JSON_HEADER)
            if response.ok:
                logging.info(f"Request to node {node_id} was successful with status code: {response.status_code}.")
            else:
                # TODO: Handle this?
                logging.error(f"Request to node {node_id} failed with status code: {response.status_code}.")

    def _choose_txs_algo(self):
        # must return CAPACITY transactions
        return "TODO"

    def next_block(self):
        b = Block(
                self.blockchain.blocks[-1].idx + 1,
                time.time(),
                self._choose_txs_algo(),
                self.public_key,
                self.blockchain.blocks[-1].hash
            )
        b.block_hash = b.hash()
        return b

    def create_tx(self, recv, type, payload):
        print(f"[Stub Method] Node {self.id} sends a transaction")

        # Accept IDs instead of public keys as well.
        if recv.isdigit():
            if self.other_nodes.get(int(recv)) is None and int(recv) != self.id:
                print(f"Specified Node [{int(recv)}] does not exist.")
                return
            recv = self.other_nodes[int(recv)].public_key if int(recv) != self.id else self.public_key

        if recv == self.public_key and type != TransactionType.STAKE.value:
            print("Cannot send transaction to sender.")
            return

        # Verify sufficient wallet
        match type:
            case TransactionType.MESSAGE.value:
                transaction_cost = len(payload)
            case TransactionType.AMOUNT.value:
                transaction_cost = payload * Constants.TRANSFER_FEE_MULTIPLIER
            case TransactionType.STAKE.value:
                transaction_cost = payload - self.stakes[self.id]
            case _:
                print("Invalid transaction type.")
                return
        if transaction_cost > self.bcc:
            print(f"Transaction cannot proceed as the node does not have the required BCCs.")
            return

        # Balance updates
        if type == TransactionType.AMOUNT.value:
            self.bcc -= transaction_cost
            recv_id = self.get_node_id_by_public_key(recv)
            self.other_nodes[recv_id].bcc += payload
            logging.info(f"Node's BCCs have been decreased to {self.bcc}.")
        elif type == TransactionType.STAKE.value:
            self.bcc -= transaction_cost
            self.stakes[self.id] = payload

        tx_request = self.tx_builder.create(recv, type, payload)
        self.broadcast_request(tx_request, "/transactions")

    def stake(self, amount):
        print(f"[Stub Method] Node {self.id} stakes {amount}")
        self.create_tx(str(Constants.BOOTSTRAP_ID), TransactionType.STAKE.value, amount)

    def view_block(self):
        print(f"[Stub Method] Node {self.id} views the last block")

    def balance(self):
        print(f"[Stub Method] Node {self.id} views its balance")

        # TODO: This is temporary for testing. To be altered.
        print(f"Stakes: {[(id, stake) for id, stake in self.stakes.items()]}.")
        print(f"BCCs: {[(node_id, node.bcc) for node_id, node in self.other_nodes.items()]}. Self BCC: {self.bcc}.")

    def execute_cmd(self, line: str):
        # lstrip to remove leading whitespace, if any
        items = line.lstrip().split(" ")
        command_name = items[0]
        match command_name:
            case "t":
                try:
                    amount = float(items[2])
                    self.create_tx(items[1], TransactionType.AMOUNT.value, amount)
                except ValueError:
                    self.create_tx(items[1], TransactionType.MESSAGE.value, items[2])
                except IndexError:
                    print("[Error] Transaction amount was not provided!")
            case "stake":
                try:
                    amount = float(items[1])
                    self.stake(amount)
                except ValueError:
                    print("[Error] Stake amount must be a number!")
            case "view":
                self.view_block()
            case "balance":
                self.balance()
            case  "help":
                print("<help shown here>")
            case _:
                print("Invalid Command! You can view valid commands with \'help\'")


