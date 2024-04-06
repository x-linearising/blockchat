from node import NodeInfo

# TODO: This follows a different logic from other request classes. We could possibly fix this and
#   have a common logic in our request classes.
class NodeListRequest:
    """
    This is the request made from Boostrap node after bootstrap phase is complete.
    It contains a list of all the nodes that entered the network (including bootstrap).
    """

    @classmethod
    def from_node_info_dict_to_request(cls, nodes_info: dict[int, NodeInfo]):
        request = []
        for node_id, node_info in nodes_info.items():
            request.append({
                "ip_address": node_info.ip_address,
                "port": node_info.port,
                "public_key": node_info.public_key,
                "id": node_id
            })
        return request

    @classmethod
    def from_request_to_node_info_dict(cls, request):
        nodes_info = {}
        for node in request:
            nodes_info[node["id"]] = NodeInfo(node["ip_address"],
                                              node["port"],
                                              node["public_key"],
                                              0)
        return nodes_info
