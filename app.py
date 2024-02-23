import logging

from flask import Flask
from flask_restful import Api

from controllers.controller import BootstrapController, NodeController
from constants import Constants

app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=logging.INFO)

is_bootstrap_str = input("Start node as bootstrap node? (y/n): ").lower()
is_bootstrap = is_bootstrap_str == 'y'

if is_bootstrap:
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

    # Set up node, basically its memory.
    node_controller = NodeController(ip_address, port)

    # Add routes / endpoints.
    app.register_blueprint(node_controller.blueprint, url_prefix='/nodes')

    app.run(port=port)
    # TODO: parse reply and do node.id = reply.id
    # TODO: node also listens on endpoints
    # (maybe split the files to bootstrap_app and node_app for this)