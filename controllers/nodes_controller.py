import logging

from flask import Blueprint, abort, request

from node import Node
from node_memory import NodeMemory
from request_classes.join_request import JoinRequest
from response_classes.join_response import JoinResponse


class NodesController:
    """
        A controller containing all the endpoints related to the Node resource.
        Should only be used for the bootstrapping phase as the network is permanent
        after that.
    """
    nodes_blueprint = Blueprint('nodes', __name__)
    nodes_counter = 1
    is_bootstrapping_phase_over = False
    max_number_of_nodes = 10

    @staticmethod
    @nodes_blueprint.route('/', methods=['POST'])
    def add_node():
        # Mapping request body to class
        join_request = JoinRequest.from_json(request.json)
        logging.info(f"Received request to add the following node to the network: {join_request.to_dict()}.")

        # Performing validations
        NodesController.perform_validations_for_post(join_request)

        # Adding node
        id_of_new_node = NodesController.nodes_counter
        new_node = Node.from_request(join_request, id_of_new_node)
        NodeMemory.add_node_to_list(new_node)
        NodesController.nodes_counter += 1
        logging.info(f"Node with id {id_of_new_node} has been added to the network.")

        if NodesController.nodes_counter > NodesController.max_number_of_nodes:
            logging.info("Reached maximum number of nodes. Sending the final node list to all participants.")
            NodesController.is_bootstrapping_phase_over = True
            # TODO: Bootstrapping complete. Broadcast appropriate message to all.

        # Creating response
        response = JoinResponse(id_of_new_node)

        return response.to_dict()

    @staticmethod
    def perform_validations_for_post(join_request: JoinRequest):
        if not NodeMemory.is_bootstrap:
            log_message = "Bad request: Not bootstrap node."
            logging.warning(log_message)
            abort(400, description=log_message)

        if NodesController.is_bootstrapping_phase_over:
            log_message = "Bad request: Bootstrapping phase is over."
            logging.warning(log_message)
            abort(400, description=log_message)

        if NodeMemory.node_already_in_list(join_request.ip_address, join_request.port):
            log_message = "Bad request: Node with given ip and port has already been added."
            logging.warning(log_message)
            abort(400, description=log_message)


