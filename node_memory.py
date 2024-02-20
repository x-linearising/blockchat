# from constants import Constants
# from node import Node


# class NodeMemory:
#     process_node = None
#     is_bootstrap = None
#     other_nodes = {}

#     @classmethod
#     def setup_node(cls):
#         is_bootstrap_str = input("Start node as bootstrap node? (y/n): ").lower()
#         is_bootstrap = is_bootstrap_str == 'y'
#         if not is_bootstrap:
#             cls.setup_as_normal_node()
#         else:
#             cls.setup_as_bootstrap_node()

#     @classmethod
#     def setup_as_bootstrap_node(cls):
#         cls.is_bootstrap = True
#         cls.process_node = Node(Constants.BOOTSTRAP_PUBLIC_KEY,
#                                 Constants.BOOTSTRAP_IP_ADDRESS,
#                                 Constants.BOOTSTRAP_PORT,
#                                 Constants.BOOTSTRAP_ID)

#     @classmethod
#     def setup_as_normal_node(cls):
#         cls.is_bootstrap = False
#         ip_address = "http://localhost"  # TODO: Replace this maybe. Find it automatically?
#         port = int(input("Enter port number: "))
#         public_key = "some public key"  # TODO: Generate a key.
#         cls.process_node = Node(public_key, ip_address, port)
#         cls.process_node.request_to_join_network_and_get_assigned_id()

#     @classmethod
#     def set_node_list(cls):
#         cls.other_nodes = ...  # TODO: Call this when bootstrap node knocks the door

#     @classmethod
#     def add_node_to_list(cls, new_node):
#         cls.other_nodes[new_node.id] = new_node

#     @classmethod
#     def node_already_in_list(cls, ip_address, port):
#         for node in cls.other_nodes.values():
#             if node.ip_address == ip_address and node.port == port:
#                 return True
#         return False