import logging
import time
import random
import requests

from helper import tx_str
from block import Block
from blockchain import Blockchain
from constants import Constants
from request_classes.block_request import BlockRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder, TransactionType


class NodeInfo:
    def __init__(self, ip_address, port, public_key=None, bcc=0):
        self.ip_address = ip_address
        self.port = port
        self.public_key = public_key
        self.bcc = bcc

    def get_node_url(self):
        url = f"http://{self.ip_address}:{self.port}"
        return url


class Node(NodeInfo):
    def __init__(self, ip_address, port, node_id=None, path=None):
        self.wallet = Wallet(path)
        self.other_nodes: dict[int, NodeInfo] = {}
        self.tx_builder = TransactionBuilder(self.wallet)
        super().__init__(ip_address, port, self.wallet.public_key)
        if node_id is None:
            self.join_network()  # TODO: Maybe move this in Controller?
        else:
            self.id = node_id
        
        self.is_validator = False
        self.transactions = []
        self.stakes = {}
        self.validated_stakes = {}
        self.expected_nonce = {}
        self.blockchain = Blockchain()

    def initialize_stakes(self):
        for node_id, node_info in self.other_nodes.items():
            self.stakes[node_id] = Constants.INITIAL_STAKE
            self.validated_stakes[node_id] = Constants.INITIAL_STAKE
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
            # Do not send a request to myself!
            if node_id == self.id:
                continue

            response = requests.post(node.get_node_url() + endpoint,
                                     json=request_body,
                                     headers=Constants.JSON_HEADER)
            if response.ok:
                # logging.info(f"Request to node {node_id} was successful with status code: {response.status_code}.")
                pass
            else:
                # TODO: Handle this?
                logging.error(f"Request to node {node_id} failed with status code: {response.status_code}.")

    def next_validator(self):

        nodes = [i for i in range(Constants.MAX_NODES)]

        stakes = [self.validated_stakes[i] for i in nodes]

        total_stake = sum(stakes)

        weights = [stakes[i]/total_stake for i in nodes]
        # print("Finding next validator with probabilities:")
        # print(weights)

        random.seed(self.blockchain.blocks[-1].block_hash)
        tmp = random.choices(nodes, weights=weights, k=1)[0]
        
        print("next validator id:", tmp)

        tmp = self.other_nodes[tmp].public_key

        return tmp


    def create_tx(self, recv, type, payload):
        # Accept IDs instead of public keys as well.
        if recv.isdigit():
            if self.other_nodes.get(int(recv)) is None:
                print(f"Specified Node [{int(recv)}] does not exist.")
                return
            recv = self.other_nodes[int(recv)].public_key

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
        print(f"Total transaction cost: {transaction_cost}")

        if transaction_cost > self.other_nodes[self.id].bcc:
            print(f"Transaction cannot proceed as the node does not have the required BCCs.")
            return

        # Balance updates
        if type == TransactionType.AMOUNT.value:
            self.other_nodes[self.id].bcc -= transaction_cost
            recv_id = self.get_node_id_by_public_key(recv)
            self.other_nodes[recv_id].bcc += payload
        elif type == TransactionType.STAKE.value:
            self.other_nodes[self.id].bcc -= transaction_cost
            self.stakes[self.id] = payload

        tx_request = self.tx_builder.create(recv, type, payload)
        self.broadcast_request(tx_request, "/transactions")
        self.transactions.append(tx_request)

    def mint_block(self):
        # create new block
        prev_block = self.blockchain.blocks[-1]
        b = Block(prev_block.idx+1, time.time(), self.transactions[:Constants.CAPACITY], self.public_key, prev_block.block_hash)
        b.set_hash()

        print("As the validator, I won {:.2f} in fees".format(b.fees()))
        self.other_nodes[self.id].bcc += b.fees()

        print("Sending block!")
        # print(b.to_str())

        self.transactions = self.transactions[Constants.CAPACITY:]
        block_request = BlockRequest.from_block_to_request(b)
        self.blockchain.add(b)
        self.broadcast_request(block_request, '/blocks')

        for staker_public_key, stake in b.stakes().items():
            if staker_public_key == self.public_key:
                self.validated_stakes[self.id] = stake
            else:
                self.validated_stakes[self.get_node_id_by_public_key(staker_public_key)] = stake

        next_validator = self.next_validator()
        self.is_validator = (next_validator == self.public_key) 

    def stake(self, amount):
        self.create_tx(str(Constants.BOOTSTRAP_ID), TransactionType.STAKE.value, amount)

    def view_block(self):
        print("Last validated block:")
        print(self.blockchain.blocks[-1].to_str())

    def balance(self):
        print("")
        print("Node   Balance  Stake    Total    Validated Stake")
        print("-------------------------------------------------")
        # line example:
        #     "10 (*) 10999.99 53.26"
        for i in range(Constants.MAX_NODES):
            c = "(*)" if i == self.id else "   "
            total = self.other_nodes[i].bcc + self.stakes[i]
            print("{:<3d}{} {:<8.2f} {:<8.2f} {:<8.2f} {:<8.2f}".format(
                i,
                c,
                self.other_nodes[i].bcc,
                self.stakes[i],
                total,
                self.validated_stakes[i]),
            )

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
            case "tx":
                print("is_validator:", self.is_validator)
                tabs = 1 * "\t"

                s = tabs + f"transactions: [\n"

                for i, tx in enumerate(self.transactions):
                    s += tx_str(tx, True, 2)
                    if i != len(self.transactions) - 1:
                        s += "\n"
                s += tabs + "]"
                print(s)
            case "balance":
                self.balance()
            case  "help":
                print("<help shown here>")
            case _:
                print("Invalid Command! You can view valid commands with \'help\'")


