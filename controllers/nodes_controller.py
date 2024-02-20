import logging

from flask import Blueprint, abort, request

from node import Node, Bootstrap
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse
from constants import Constants 


class BootstrapController:
    
    def __init__(self):
        self.bootstrap = Bootstrap(Constants.BOOTSTRAP_IP_ADDRESS, Constants.BOOTSTRAP_PORT)
        self.blueprint = Blueprint("nodes", __name__)
        self.nodes_counter = 1
        self.is_bootstrapping_phase_over = False
        # equivalent to using @self.blueprint.route on add_node
        # (which wouldn't work because of the self prefix)
        self.blueprint.add_url_rule("/", "nodes", self.add_node, methods=["POST"])

    def add_node(self):
        """
        Method that gets called when a node sends a POST request at the /nodes endpoint
        Adds the node's info (public key, ip, port) to the bootstraps node list and
        returns the node's assigned id.
        """

        # Mapping request body to class
        join_request = JoinRequest.from_json(request.json)
        logging.info(f"Received request to add the following node to the network: {join_request.to_dict()}.")

        # Performing validations
        self.validate_request(join_request)

        # Adding node
        self.bootstrap.add_node(join_request, self.nodes_counter)
        logging.info(f"Node with id {self.nodes_counter} has been added to the network.")

        # Creating response
        response = JoinResponse(self.nodes_counter)
        self.nodes_counter += 1

        # Check if every expected node has joined
        if self.nodes_counter > Constants.MAX_NODES:
            logging.info("Reached maximum number of nodes. Sending the final node list to all participants.")
            self.is_bootstrapping_phase_over = True
            # TODO: Bootstrapping complete. Broadcast appropriate message to all.

        return response.to_dict()

    def validate_request(self, request: JoinRequest):
        if self.is_bootstrapping_phase_over:
            log_message = "Bad request: Bootstrapping phase is over."
            logging.warning(log_message)
            abort(400, description=log_message)

        if self.bootstrap.node_has_joined(request.ip_address, request.port):
            log_message = "Bad request: Node with given ip and port has already been added."
            logging.warning(log_message)
            abort(400, description=log_message) 


# class NodesController:
#     """
#         A controller containing all the endpoints related to the Node resource.
#         Should only be used for the bootstrapping phase as the network is permanent after that.
#     """
#     nodes_blueprint = Blueprint('nodes', __name__)
#     nodes_counter = 1
#     is_bootstrapping_phase_over = False
#     max_number_of_nodes = 10

#     @staticmethod
#     @nodes_blueprint.route('/', methods=['POST'])
#     def add_node():
#         # Mapping request body to class
#         join_request = JoinRequest.from_json(request.json)
#         logging.info(f"Received request to add the following node to the network: {join_request.to_dict()}.")

#         # Performing validations
#         NodesController.perform_validations_for_post(join_request)

#         # Adding node
#         id_of_new_node = NodesController.nodes_counter
#         new_node = Node.from_request(join_request, id_of_new_node)
#         NodeMemory.add_node_to_list(new_node)
#         NodesController.nodes_counter += 1
#         logging.info(f"Node with id {id_of_new_node} has been added to the network.")

#         if NodesController.nodes_counter > NodesController.max_number_of_nodes:
#             logging.info("Reached maximum number of nodes. Sending the final node list to all participants.")
#             NodesController.is_bootstrapping_phase_over = True
#             # TODO: Bootstrapping complete. Broadcast appropriate message to all.

#         # Creating response
#         response = JoinResponse(id_of_new_node)

#         return response.to_dict()