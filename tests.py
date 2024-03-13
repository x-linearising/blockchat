from constants import Constants


def validate_that_blockchains_are_identical():
    with open("logs/blockchain0.txt", 'r') as file1:
        content1 = file1.read()
    for j in range(1, Constants.MAX_NODES):
        with open(f"logs/blockchain{j}.txt", 'r') as file2:
            content2 = file2.read()
            if content1 != content2:
                print("Blockchains are not the same! :(")
                return
    print("All blockchains are identical! :D")
    return

def validate_that_file_does_not_have_duplicate_transactions(index, transactions_per_block):
    with open(f"logs/blockchain{index}.txt", 'r') as file1:
        data = file1.read()
    parsed_transactions = []
    current_section = None
    current_transaction = {}
    block_transactions = 0
    sender_counts = {}
    is_first_block = True
    for line in data.split('\n'):
        line = line.strip()
        if "transactions" in line:
            current_section = "transactions"
        elif current_section == "transactions":
            if ":" in line:
                key, value = line.split(': ')
                current_transaction[key] = value
            elif "]" not in line:
                block_transactions +=1
                sender = current_transaction["sender_addr"]
                if sender_counts.get(sender) is None:
                    sender_counts[sender] = 1
                else:
                    sender_counts[sender] += 1
                parsed_transactions.append(current_transaction)
                current_transaction = {}
            elif "]" in line:
                block_transactions +=1
                sender = current_transaction["sender_addr"]
                if sender_counts.get(sender) is None:
                    sender_counts[sender] = 0
                else:
                    sender_counts[sender] += 1
                parsed_transactions.append(current_transaction)
                current_transaction = {}
                current_section = "other"
                if block_transactions != transactions_per_block and not is_first_block:
                    is_first_block = False
                    print("Wrong number of transactions detected in block.")
                block_transactions = 0

    print("Transactions sent per sender: ")
    print(sender_counts)

    for i, t1 in enumerate(parsed_transactions):
        for j, t2 in enumerate(parsed_transactions):
            if i <= j:
                continue
            if t1["sender_addr"] == t2["sender_addr"] and t1["recv_addr"] == t2["recv_addr"] and t1["nonce"] == t2["nonce"]:
                print("Duplicate transaction detected.")
                print(t1)
                print(t2)
                return True
    print("No duplicate transactions were detected.")
    return False

if __name__ == "__main__":
    validate_that_blockchains_are_identical()
    validate_that_file_does_not_have_duplicate_transactions(0, Constants.CAPACITY)

