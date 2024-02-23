import logging
import argparse
from threading import Thread

from flask import Flask
from flask_restful import Api
from controllers.controller import BootstrapController, NodeController
from node import Node, Bootstrap
from constants import Constants
from helper import myIP

app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrap", action = argparse.BooleanOptionalAction, default = False)
parser.add_argument("-p", "--port", nargs = "?", const = "8000", default = "8000")
args = parser.parse_args()

is_bootstrap = args.bootstrap

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

if is_bootstrap:
    # Set up node, basically its memory.
    bootstrap = BootstrapController()

    # Add routes / endpoints.
    app.register_blueprint(bootstrap.blueprint, url_prefix='/nodes')

    # Run the API

    print(f"Bootstrap has joined the network.")
    app.run(host="0.0.0.0", port=Constants.BOOTSTRAP_PORT)
else:
    # Set up node, basically its memory.
    node_controller = NodeController(myIP(), args.port)

    # Add routes / endpoints.
    app.register_blueprint(node_controller.blueprint, url_prefix='/nodes')

    app_thread = Thread(target=lambda: app.run(args.port))
    app_thread.run()

    try:
        while True:
            print(f"[Node {node_controller.node.id}] Enter your command:")
            line = input(">>> ")
            node_controller.node.execute_cmd(line)
    except KeyboardInterrupt:
        print("Shutting down app and cli.")
    # TODO: node also listens on endpoints
    # (maybe split the files to bootstrap_app and node_app for this)