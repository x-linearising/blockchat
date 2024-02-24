import logging
import argparse

from flask import Flask
from flask_restful import Api
from controllers.controller import BootstrapController, NodeController
from constants import Constants
from helper import myIP

app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument("-b", "--bootstrap", action = argparse.BooleanOptionalAction, default = False)
parser.add_argument("-p", "--port", nargs = "?", const = "8000", default = "8000")
args = parser.parse_args()
# args.bootstrap = True if args.port == '5000' else False

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

# Set up node, basically its memory.
controller = BootstrapController() if args.bootstrap else NodeController(myIP(), args.port)

# Add routes / endpoints.
app.register_blueprint(controller.blueprint, url_prefix='/')

app.run(host="0.0.0.0", port=Constants.BOOTSTRAP_PORT if args.bootstrap else args.port)

# TODO: Run cli in separate process (merged on master, ignore this.)

# try:
#     while True:
#         print(f"[Node {controller.node.id}] Enter your command:")
#         line = input(">>> ")
#         controller.node.execute_cmd(line)
# except KeyboardInterrupt:
#     print("Shutting down app and cli.")

# (maybe split the files to bootstrap_app and node_app for this)