from bootstrap import Bootstrap
from request_classes.blockchain_request import BlockchainRequest


if __name__ == "__main__":
    b = Bootstrap()
    bc = b.blockchain

    br = BlockchainRequest(bc)

    # print(b.blockchain.blocks)

