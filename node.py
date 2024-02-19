import requests

from constants import Constants
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse


class Node:
    def __init__(self, public_key, ip_address, port, id=None):
        self.id = id
        self.public_key = public_key
        self.ip_address = ip_address
        self.port = port

    @classmethod
    def from_request(cls, join_request: JoinRequest, id: int):
        """
            Creates a Node object from the data of a join request.
            Assigns to the node the id specified (locally).
        """
        return cls(join_request.public_key, join_request.ip_address, join_request.port, id)

    def request_to_join_network_and_get_assigned_id(self):
        """
            Makes a request to the boostrap node in order to join the network.
            If the join is successful, the node is assigned an id.
        """

        # Make request to boostrap node
        request = JoinRequest(self.public_key, self.ip_address, self.port)

        # Set the headers with the appropriate Content-Type
        headers = {'Content-Type': 'application/json'}

        raw_response = requests.post(Constants.get_bootstrap_node_url() + "/nodes", json=request.to_dict(),
                                     headers=headers)
        response = JoinResponse.from_json(raw_response.json())

        # Assign returned id to node
        self.id = response.id
