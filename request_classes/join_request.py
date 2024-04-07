from helper import JSONSerializable


class JoinRequest(JSONSerializable):
    """
    This is the request made to the Boostrap node from a node that wishes to enter the network.
    It contains the necessary info the Boostrap node should forward to other nodes
    so that they can communicate with the new node.
    """
    def __init__(self, public_key, ip_address, port):
        self.public_key = public_key
        self.ip_address = ip_address
        self.port = port

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data.get('public_key'),
                   json_data.get('ip_address'),
                   json_data.get('port'))
