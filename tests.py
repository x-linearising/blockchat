#!/usr/bin/env python3
import sys
import yaml
from constants import Constants

def val_identical_blockchains():
    with open("logs/blockchain0.txt", 'r') as file1:
        content1 = file1.read()
    for j in range(1, Constants.MAX_NODES):
        with open(f"logs/blockchain{j}.txt", 'r') as file2:
            content2 = file2.read()
            if content1 != content2:
                return None
    return yaml.safe_load(content1)["blockchain"]

def val_no_dup_blocks(blockchain):
    hashes = []
    for b in blockchain:
        if b["hash"] in hashes:
            return b["index"]
        else:
            hashes.append(b["hash"])
    return -1

def val_no_dup_tx(blockchain):
    hashes = []
    for b in blockchain:
        for tx in b["transactions"]:
            if tx["hash"] in hashes:
                return tx["hash"], b["index"]
            else:
                hashes.append(tx["hash"])
    return (-1, -1)

if __name__ == "__main__":
    blockchain =  val_identical_blockchains()
    if blockchain is None:
        print("[ERROR] Blockchains are not the same! :(")
        sys.exit(-1)
    else:
        print("[OK] All blockchains are identical! :D")

    idx = val_no_dup_blocks(blockchain)
    if  idx == -1:
        print("[OK] Blockchain has no identical blocks.")
    else:
        print(f"[ERROR] Block with index {idx} is a duplicate.")
        sys.exit(-1)

    tx, idx = val_no_dup_tx(blockchain)
    if tx == -1 and idx == -1:
        print("[OK] No duplicate transactions detected.")
    else:
        print(f"[ERROR] In block {idx}: Tx {tx} is a duplicate.")


