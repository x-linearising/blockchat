import logging
import time
import random
import requests
import sys
import os
from functools import reduce
from random import randint
from threading import Thread, Lock

from helper import tx_str, url_str, read_transaction_file, BootstrapConnError
from block import Block
from blockchain import Blockchain
from constants import Constants
from request_classes.block_request import BlockRequest
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from wallet import Wallet
from transaction import TransactionBuilder, TransactionType, tx_cost

my_tx = 0

class NodeInfo:
    def __init__(self, ip_address, port, public_key=None, bcc=0):
        self.ip_address = ip_address
        self.port = port
        self.public_key = public_key
        self.bcc = bcc


class Node:
    def __init__(self, ip_address, port, node_id=None, path=None, read_file=True):
        self.wallet = Wallet(path)
        self.tx_builder = TransactionBuilder(self.wallet)
        self.public_key = self.wallet.public_key
        self.my_info = None
        self.all_nodes: dict[int, NodeInfo] = {}
        self.pending_tx = set()
        self.hard_bcc = {}
        self.pending_blocks = {}
        
        # Only the bootstrap node creates a Node object with known id
        if node_id is None:
            self.join_network(ip_address, port, self.public_key)  # TODO: Maybe move this in Controller?
        else:
            self.id = node_id
        
        self.transactions = []
        self.soft_stakes = {}
        self.hard_stakes = {}
        self.soft_nonce = {}
        self.hard_nonce = {}

        self.blockchain = Blockchain()
        # Keep a list of which node (by id) validated each block for testing
        self.validators = []
        self.lock = Lock()
        self.mint_broadcast_lock = Lock()
        thr = Thread(target=self.poll_capacity)
        thr.start()
        if read_file:
            thr2 = Thread(target=self.poll_done)
            thr2.start()
 
    def poll_capacity(self):
        # Do not start minting until all nodes have received their BCCs.
        while self.soft_nonce.get(Constants.BOOTSTRAP_ID) is None or self.soft_nonce.get(Constants.BOOTSTRAP_ID) < Constants.MAX_NODES:
            time.sleep(1)
        time.sleep(1)
        blocks_competed_for = 1
        while True:
            # print(f"is_next_validator {self.is_next_validator()}!!")
            if blocks_competed_for <= len(self.blockchain.blocks) and len(self.transactions) >= Constants.CAPACITY:
                if self.is_next_validator(blocks_competed_for - 1):
                    self.mint_block()
                blocks_competed_for += 1
            else:
                # yield
                time.sleep(0)

    def poll_done(self):
        """
        Thread function that polls the length of the blockchain every 3 seconds.
        When it stops growing, assume that the message passing is finished and
        dump logs.
        """
        # Wait until all nodes have connected to the network
        while len(self.all_nodes) != Constants.MAX_NODES:
            time.sleep(1)
        
        last_len = 0
        while True:
            cur_len = len(self.blockchain)
            if cur_len == last_len:
                print("!!! DUMPING LOGS !!!")
                self.dump_logs()
                break
            else:
                last_len = cur_len
                time.sleep(3)

    def initialize_stakes(self):
        for node_id, node_info in self.all_nodes.items():
            self.soft_stakes[node_id] = Constants.INITIAL_STAKE
            self.hard_stakes[node_id] = Constants.INITIAL_STAKE
            self.all_nodes[node_id].bcc -= Constants.INITIAL_STAKE
            self.hard_bcc[node_id] -= Constants.INITIAL_STAKE
        return self.soft_stakes

    def get_node_info_by_public_key(self, public_key):
        for node_info in self.all_nodes.values():
            if node_info.public_key == public_key:
                return node_info

    def get_node_id_by_public_key(self, public_key):
        for node_id, node_info in self.all_nodes.items():
            if node_info.public_key == public_key:
                return node_id

    def join_network(self, ip, port, pubkey):
        """
        Makes a request to the boostrap node in order to join the network.
        If the join is successful, the node is assigned an id.
        """

        logging.info("Sending request to Boostrap Node to join the network.")

        # Make request to boostrap node
        join_request = JoinRequest(pubkey, ip, port)

        try:
            join_response = requests.post(
                url_str(Constants.BOOTSTRAP_IP_ADDRESS, Constants.BOOTSTRAP_PORT) + "/nodes",
                json=join_request.to_dict(),
                headers=Constants.JSON_HEADER,
            )
        except requests.exceptions.ConnectionError:
            raise BootstrapConnError("Connection to bootstrap node failed -- is it running?")

        if join_response.ok:
            response = JoinResponse.from_json(join_response.json())
            self.id = response.id
            print(f"Joined the network successfully with id {self.id}. Waiting for bootstrap phase completion.")
        else:
            raise BootstrapConnError(join_response.text)

    def broadcast_request(self, request_body, endpoint):
        for node_id, node in self.all_nodes.items():
            # Do not send a request to myself!
            if node_id == self.id:
                continue

            # if endpoint == "/blocks":
                # print(f"Sending block to {node_id}")

            response = requests.post(url_str(node.ip_address, node.port) + endpoint,
                                     json=request_body,
                                     headers=Constants.JSON_HEADER)

            if response.ok:
                # logging.info(f"Request to node {node_id} was successful with status code: {response.status_code}.")
                pass
            else:
                # TODO: Handle this?
                logging.warning(f"REQ TO {node_id} FAILED: [{response.status_code}]: {response.reason}.")
                # sys.exit()  # TODO: This is causing trouble. Transaction file reading stops here.

    def is_next_validator(self, idx=-1):
        return self.next_validator(idx) == self.public_key

    def next_validator(self, idx=-1):
        prev_block = self.blockchain.blocks[idx]

        nodes = [i for i in range(Constants.MAX_NODES)]
        stakes = [self.hard_stakes[i] for i in nodes]

        total_stake = sum(stakes)

        weights = [stakes[i]/total_stake for i in nodes]

        random.seed(prev_block.block_hash)
        i = random.choices(nodes, weights=weights, k=1)[0]
        
        self.validators.append(i)
        return self.all_nodes[i].public_key


    def create_tx(self, recv, type, payload):
        global my_tx

        # Accept IDs instead of public keys as well.
        if recv.isdigit():
            if self.all_nodes.get(int(recv)) is None:
                print(f"Specified Node [{int(recv)}] does not exist.")
                return
            recv = self.all_nodes[int(recv)].public_key

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
                transaction_cost = payload - self.soft_stakes[self.id]
            case _:
                print("Invalid transaction type.")
                return

        self.lock.acquire()
        self.mint_broadcast_lock.acquire()
        my_tx += 1
        logging.info("[CREATE TX {}] Cost: {} My balance: {} My val balance: {}".format(
            my_tx,
            transaction_cost,
            self.my_info.bcc,
            self.hard_bcc[self.id]
        ))

        if transaction_cost > self.my_info.bcc:
            self.lock.release()
            self.mint_broadcast_lock.release()
            logging.warn(f"My Transaction cannot proceed as the node does not have the required BCCs.")
            # time.sleep(5)
            return

        # Balance updates
        self.my_info.bcc -= transaction_cost
        if type == TransactionType.AMOUNT.value:
            recv_id = self.get_node_id_by_public_key(recv)
            self.all_nodes[recv_id].bcc += payload
        elif type == TransactionType.STAKE.value:
            self.soft_stakes[self.id] = payload

        tx_request = self.tx_builder.create(recv, type, payload)

        logging.info("[CREATE TX {}] Hash: {}".format(my_tx, tx_request["hash"]))

        self.transactions.append(tx_request)
        # print("\nMY TX HASHES:")
        # for tx in self.transactions:
        #     print(tx["hash"])
        # print("\n")

        self.lock.release()
        self.mint_broadcast_lock.release()
        self.broadcast_request(tx_request, "/transactions")

    def mint_block(self):
        """
        Method called by the validator node.
        Remove the oldest `capacity` received transactions, create a block from
        them and send it to the rest of the nodes.
        """
        self.lock.acquire()
        prev_block = self.blockchain.blocks[-1]
        block_txs = self.transactions[:Constants.CAPACITY]
        # print("[MINT BLOCK] WITH TXS:")
        # for tx in block_txs:
        #     print(tx["hash"])

        # Prune txs added to the block from this node's list
        self.transactions = self.transactions[Constants.CAPACITY:]

        b = Block(prev_block.idx+1, time.time(), block_txs, self.public_key, prev_block.block_hash)
        b.set_hash()

        logging.info(f"[MINT BLOCK] idx: {prev_block.idx+1}")

        # Update the amount of validated BCCs for each node.
        for tx in block_txs:
            sender_id = self.get_node_id_by_public_key(tx["contents"]["sender_addr"])
            self.hard_bcc[sender_id] -= tx_cost(tx["contents"], self.hard_stakes[sender_id])

            if tx["contents"]["type"] == TransactionType.STAKE.value:
                self.hard_stakes[sender_id] = tx["contents"]["amount"]
            if tx["contents"]["type"] == TransactionType.AMOUNT.value:
                recv_pubkey = tx["contents"]["recv_addr"]
                recv_id = self.get_node_id_by_public_key(recv_pubkey)
                self.hard_bcc[recv_id] += tx["contents"]["amount"]

        # print("As the validator, I won {:.2f} in fees. Sending block...".format(b.fees()))
        self.my_info.bcc += b.fees()
        self.hard_bcc[self.id] += b.fees()

        block_request = BlockRequest.from_block_to_request(b)
        self.blockchain.add(b)

        self.lock.release()

        self.mint_broadcast_lock.acquire()
        self.broadcast_request(block_request, '/blocks')
        self.mint_broadcast_lock.release()

    def stake(self, amount):
        self.create_tx(str(Constants.BOOTSTRAP_ID), TransactionType.STAKE.value, amount)
        print(f"Node {self.id} stakes {amount}")

    def view_block(self):
        return self.blockchain.blocks[-1].to_str()

    def read_simple_transaction_file(self):
        receivers = []
        messages = []
        with open("input/transez.txt", "r") as f:
            lines = f.readlines()
            for line in lines:
                recv_id = randint(0, Constants.MAX_NODES)
                while recv_id == self.id:
                    recv_id = randint(0, Constants.MAX_NODES)
                receivers.append(recv_id)
                messages.append(line)

        return receivers, messages


    def execute_file_transactions(self):
        receivers, messages = read_transaction_file(self.id)
        # receivers, messages = self.read_simple_transaction_file()
        for receiver, message in zip(receivers, messages):
            # time.sleep(0.1 + random.random())

            if receiver > Constants.MAX_NODES - 1:
                continue

            self.create_tx(self.all_nodes[receiver].public_key, TransactionType.MESSAGE.value, message[:-1])

    def dump_logs(self):
        # Create log directory if it doesn't exist
        log_path = os.path.join(Constants.SRC_PATH, "logs")
        if not os.path.exists(log_path):
            os.mkdir(log_path)

        # fname = "validators" + str(self.id) + ".txt"
        # fpath = path.join(".", "logs", fname)
        # with open(fpath, "w") as f:
        #     for v in self.validators:
        #         f.write(str(v) + "\n")
        
        fname = "blockchain" + str(self.id) + ".txt"
        fpath = os.path.join(log_path, fname)
        with open(fpath, "w") as f:
            f.write(self.blockchain.to_str())

        fname = "balance" + str(self.id) + ".txt"
        fpath = os.path.join(log_path, fname)
        with open(fpath, "w") as f:
            f.write(self.balance(add_mark=False))  

    def waiting_tx_fees(self):
        fees = 0
        for tx in self.transactions:
            match tx["contents"]["type"]:
                case TransactionType.AMOUNT.value:
                    fees += tx["contents"]["amount"] * (Constants.TRANSFER_FEE_MULTIPLIER - 1)
                case TransactionType.MESSAGE.value:
                    fees += len(tx["contents"]["message"])
        return fees

    def balance(self, add_mark=True):
        """
        Returns a string consisting of a table with the BCC balance and stake
        of each node, at both their "hard" (verified in the blockchain)
        and "soft" versions" (not yet verified).

        If add_mark is True, the line corresponding to this node is marked
        with a star.
        """
        s  = "Node   Balance   Stake   Total   Val. Balance   Val. Stake\n"
        s += "==========================================================\n"
        total = []
        for i in range(Constants.MAX_NODES):
            c = "(*)" if add_mark and i == self.id else "   "
            total.append(self.all_nodes[i].bcc + self.soft_stakes[i])
            s += "{:<3d}{} {:<7.2f}   {:<7.2f} {:<7.2f} {:<14.2f} {:<9.2f}\n".format(
                i,
                c,
                self.all_nodes[i].bcc,
                self.soft_stakes[i],
                total[i],
                self.hard_bcc[i],
                self.hard_stakes[i]
            )
        s += "------------------------------------------------------------>(+)\n"
        s += "Total  {:<7.2f}   {:<7.2f} {:<7.2f} {:<14.2f} {:<9.2f}\n".format(
            reduce(lambda x,y: x+y, map(lambda d: d.bcc, self.all_nodes.values())),
            reduce(lambda x,y: x+y, self.soft_stakes.values()),
            sum(total),
            reduce(lambda x,y: x+y, self.hard_bcc.values()),
            reduce(lambda x,y: x+y, self.hard_stakes.values())
        )
        s += "Next val. will earn:     {:<7.2f}\n".format(self.waiting_tx_fees())
        s += "Total circulating BCCs:  {:<7.2f}\n".format(sum(total) + self.waiting_tx_fees())

        return s

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
                if len(items) > 1 and items[1] == "all":
                    s = self.blockchain.to_str() 
                else:
                    s = self.view_block()
                print(s, end="")
                # print("validators: {}".format(self.validators))
            case "tx":
                len_sum = 0
                s = "transactions:\n"

                for i, tx in enumerate(self.transactions):
                    s += tx_str(tx, True)
                    if tx["contents"]["type"] == TransactionType.MESSAGE.value:
                        len_sum += len(tx["contents"]["message"])
                print(s)
                print(f"Sum of lengths of messages = {len_sum}")
                print(f"TX List length = {len(self.transactions)}")
            case "balance":
                print("\n" + self.balance())
            case "logs":
                self.dump_logs()
                print("Dumped logs.")
            case  "help":
                print("<help shown here>")
            case _:
                print("Invalid Command! You can view valid commands with \'help\'")


