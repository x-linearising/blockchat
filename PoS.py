import random 
random.seed(42)
from constants import Constants
# Implementing the Proof of Stake consensus mechanism,
# to find the block validator

"""
    Kathe node exei to accounts state (list) me :
    1. ypoloipo kathe node
    2. stake kathe node sto current block

    Oloi oi nodes, otan lambanoun kapoio transaction, prepei na enimerwsoyn
    to ypoloipo tou sender
    Oloi oi node, otan lambanoun minima oti egine block validation, prepei na
    prosthesoyn ta fees pou exoun kratithei apo ola ta block transactions (
    apostoli  xrimatwn + minimata), sto balance tou validator
"""

"""
    Gia na kanei stake kapoios node ena poso, prepei na kanei transaction,
    me (receiver_address = 0, stacked amount).
    Epeita, ta stakes ginontai store se ena dict typou: {id:staked amount}
"""
# stakes = {'1' : 5,
#           '2' : 10,
#           '3' : 12,
#           '4' : 25,
#           '5' : 20,
#           }

class PoS:
    def __init__(self, stakes):
        self.stakes = stakes
        self.total_stake = sum(stakes.values()) # total amount staked
        # dict with weight of every node, based on its staked amount
        self.weights = {node_id: stake / self.total_stake for node_id, stake in stakes.items()}

    def select_validator(self):
        # convert dict to tuple (node,weight)
        nodes, weights = zip(*self.weights.items())
        validator_node = random.choices(nodes, weights=weights, k=1)[0]
        # return validator_node
        return Constants.BOOTSTRAP_PUBKEY

