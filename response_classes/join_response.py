from helper import JSONSerializable


class JoinResponse(JSONSerializable):
    """
        This is the response returned by the Boostrap node to a node that requested to enter the network.
        It contains the id assigned to the new node.
    """
    def __init__(self, id):
        self.id = id

    @classmethod
    def from_json(cls, json_data):
        return cls(json_data.get('id'))

