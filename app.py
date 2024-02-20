import logging

from flask import Flask
from flask_restful import Api

from controllers.nodes_controller import BootstrapController
from node import Node, Bootstrap
from node_memory import NodeMemory
from constants import Constants

is_bootstrap_str = input("Start node as bootstrap node? (y/n): ").lower()
is_bootstrap = is_bootstrap_str == 'y'

if is_bootstrap:
    app = Flask(__name__)
    api = Api(app)
    logging.basicConfig(level=logging.INFO)

    # Set up node, basically its memory.
    bootstrap = BootstrapController()

    # Add routes / endpoints.
    app.register_blueprint(bootstrap.blueprint, url_prefix='/nodes')
    
    # Run the API
    print("-----------------------------------------------------------")
    print("""
    ____  _            _        _           _   
    |  _ \| |          | |      | |         | |  
    | |_) | | ___   ___| | _____| |__   __ _| |_ 
    |  _ <| |/ _ \ / __| |/ / __| '_ \ / _` | __|
    | |_) | | (_) | (__|   < (__| | | | (_| | |_ 
    |____/|_|\___/ \___|_|\_\___|_| |_|\__,_|\__|
    """)
    print("-----------------------------------------------------------")
    print(f"Bootstrap has joined the network.")
    app.run(port=Constants.BOOTSTRAP_PORT)
else:
    ip_address = "http://localhost"  # TODO: Replace this maybe. Find it automatically?
    port = int(input("Enter port number: "))
    node = Node(ip_address, port)
    node.request_to_join_network_and_get_assigned_id()
    # TODO: parse reply and do node.id = reply.id
    # TODO: node also listens on endpoints
    # (maybe split the files to bootstrap_app and node_app for this)