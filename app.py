#!/usr/bin/env python3

import logging
import argparse
from threading import Thread
from flask import Flask
from flask_restful import Api
from controllers.controller import BootstrapController, NodeController
from constants import Constants
from helper import myIP

def user_interface(node, prompt_str=">>> "):
    while True:
        print(f"[Node {node.id}] Enter your command:")
        line = input(prompt_str)
        node.execute_cmd(line)
        print("")

app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('werkzeug')
log.setLevel(logging.WARNING)

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

controller = BootstrapController() if args.bootstrap else NodeController(myIP(), args.port)

# Add routes / endpoints.
app.register_blueprint(controller.blueprint, url_prefix='/')
app.after_request(controller.after_request)

t = Thread(target=user_interface, args=[controller.node, ""])
t.start()
app.run(host="0.0.0.0", port=Constants.BOOTSTRAP_PORT if args.bootstrap else args.port)