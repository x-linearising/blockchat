import logging

from flask import Flask
from flask_restful import Api

from controllers.nodes_controller import NodesController
from node_memory import NodeMemory

app = Flask(__name__)
api = Api(app)
logging.basicConfig(level=logging.INFO)

# Add routes / endpoints.
app.register_blueprint(NodesController.nodes_blueprint, url_prefix='/nodes')

# Set up node, basically its memory.
NodeMemory.setup_node()

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
print(f"Node has joined the network {'as bootstrap node ' if NodeMemory.is_bootstrap else ''}with id: {NodeMemory.process_node.id}.")
app.run(port=NodeMemory.process_node.port)

