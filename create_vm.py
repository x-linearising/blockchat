from time import sleep

import requests

SERVERS_ENDPOINT = "https://cyclades.okeanos-knossos.grnet.gr/compute/v2.0/servers"
AUTH_HEADER_NAME = "X-Auth-Token"
TOKEN = ...  # TODO: Place your token here.

HEADERS = {
    AUTH_HEADER_NAME: TOKEN,
    "Content-Type": "application/json"
}

CREATION_BODY = """{
    "server": {
        "name": "My Ubuntu Jammy Cloud LTS server",
        "imageRef": "30cc96aa-9f07-4209-9853-c7ea7171795c",
        "flavorRef": 260,
        "metadata": {
            "OS": "ubuntu",
            "users": "ubuntu"
        },
        "project": "1c989b60-5d83-47ff-85b5-952a4515c4a0",
        "SNF:key_names": [],
        "networks": []
    }
}"""

CREATION_BODY_BIG_DATA = """{
    "server": {
        "name": "slave",
        "imageRef": "eca2f4ef-b428-4096-a47d-29ddf5ed68d9",
        "flavorRef": 263,
        "metadata": {
            "OS": "ubuntu",
            "users": "user"
        },
        "project": "a7cb546c-7e85-46cc-8399-29489aa403c4",
        "SNF:key_names": [],
        "networks": []
    }
}
"""


def get_status_of_server(id):
    response = requests.get(
        url=f"{SERVERS_ENDPOINT}/{id}",
        headers=HEADERS
    )
    status = response.json()["server"]["status"]
    print(f"Status of VM {id} is [{status}].")
    return status


def delete_server(id):
    requests.delete(
        url=f"{SERVERS_ENDPOINT}/{id}",
        headers=HEADERS
    )

    print(f"Requested deletion of VM {id}. Waiting for permanent deletion.")

    while get_status_of_server(id) != "DELETED":
        sleep(1)

    print(f"VM {id} has been permanently deleted.")


def create_server():
    post_response = requests.post(
        url=SERVERS_ENDPOINT,
        headers=HEADERS,
        data=CREATION_BODY_BIG_DATA
    )
    id = post_response.json()["server"]["id"]
    password = post_response.json()["server"]["adminPass"]
    print(f"Created VM with id {id} and pass {password}.")
    print(f"Waiting for build phase to complete.")

    while get_status_of_server(id) == "BUILD":
        sleep(1)
    return id


while True:
    print("Creating new VM")
    new_server_id = create_server()
    server_status = get_status_of_server(new_server_id)
    if server_status == "ERROR":
        delete_server(new_server_id)
    else:
        print("WOW")
        break
