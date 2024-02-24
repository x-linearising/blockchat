import logging

import requests

from blockchain import Blockchain
from constants import Constants
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder


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
        self.other_nodes = {}
        self.tx_builder = TransactionBuilder(self.wallet)
        super().__init__(ip_address, port, self.wallet.public_key)
        if node_id is None:
            self.join_network()  # TODO: Maybe move this in Controller?
        else:
            self.id = node_id
        self.blockchain = Blockchain()
        self.transactions = []


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


    def create_tx(self, recv, type, payload):
        print(f"[Stub Method] Node {self.id} sends a transaction")

    def stake(self, amount):
        print(f"[Stub Method] Node {self.id} stakes {amount}")

    def view_block(self):
        print(f"[Stub Method] Node {self.id} views the last block")

    def balance(self):
        print(f"[Stub Method] Node {self.id} views its balance")

    def execute_cmd(self, line: str):
        # remove leading whitespace, if any
        line = line.lstrip()
        if line.startswith("t "):
            items = line.split(" ")
            try:
                amount = float(items[2])
                self.create_tx(items[1], "a", amount)
            except ValueError:
                self.create_tx(items[1], "m", items[2])
        elif line.startswith("stake "):
            items = line.split(" ")
            try:
                amount = float(items[1])
                self.stake(amount)
            except ValueError:
                print("[Error] Stake amount must be a number!")
        elif line == "view":
            self.view_block()
        elif line == "balance":
            self.balance()
        elif line == "help":
            print("<help shown here>")
        else:
            print("Invalid Command! You can view valid commands with \'help\'")


