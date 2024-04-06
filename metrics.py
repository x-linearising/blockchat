#!/usr/bin/env python3
import os
import yaml

if __name__ == "__main__":
    LOGS = os.path.join("logs", "blockchain0.txt")
    with open(LOGS, "r") as f:
        contents = f.read()
    contents = yaml.safe_load(contents)
    blockchain = contents["blockchain"]

    # Don't take the genesis block into account
    n_blocks = len(blockchain) - 1
    # Every block contains the same amount of transactions
    capacity = len(blockchain[1]["transactions"])

    avg_block_time = (blockchain[n_blocks - 1]["timestamp"] - blockchain[1]["timestamp"]) / n_blocks
    avg_tx_time = avg_block_time / capacity

    validator_counts = {}
    for i, block in enumerate(blockchain):
        # skip the genesis block
        if i == 0:
            continue
        try:
            validator_counts[block["validator"]] += 1
        except KeyError:
            validator_counts[block["validator"]] = 1

    print("Average block time (sec): {:2f}".format(avg_block_time))
    print("Throughput (TX/sec)     : {:2f}".format(1/avg_tx_time))

    for k, v in validator_counts.items():
        print("Node {} validated {} blocks".format(k, v))

