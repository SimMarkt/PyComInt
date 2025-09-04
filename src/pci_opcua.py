"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

pci_opcua.py:
> Implements the OPC UA connection
----------------------------------------------------------------------------------------------------
"""

# pylint: disable=no-member, broad-exception-caught, broad-exception-raised

import logging

import yaml
from opcua import Client
 
class OPCUAConnection:
    """ Handles the OPCUA connection and operations. """
    def __init__(self):
        try:
            # Load OPCUA configuration
            with open("config/config_opcua.yaml", "r", encoding="utf-8") as env_file:
                    self.opcua_config = yaml.safe_load(env_file)
            self.client = None
        except Exception as e:
            logging.error("Failed to load OPCUA configuration: %s", e)

    def connect(self):
        """
            Establishes the connection to the OPCUA server.
        """
        try:
            self.client = Client(self.opcua_config['URL'])
            # Set user credentials directly
            self.client.set_user(self.opcua_config['USERNAME'])
            self.client.set_password(self.opcua_config['PASSWORD'])

            self.client.connect()
            logging.info("Connected to OPC UA server at %s as %s", self.opcua_config['URL'], self.opcua_config['USERNAME'])
        except Exception as e:
            logging.error("OPC UA connection failed: %s", e)
            self.client = None  # Mark as unavailable

    def is_connected(self):
        """
            Checks if the OPCUA connection is active.
            :return: True if connected, False otherwise.
        """
        return self.client is not None
        
    def read_node_values(self, type='AllNodes'):
        """
            Reads the values of multiple nodes using their NodeIDs.
            :param type: Reading type > either 'AllNodes' for reading all OPCUA nodes or 'H2' for reading only the hydrogen volume flow rate (for PEMEL control)
            :return values: Dictionary with node IDs as keys and their corresponding values (or errors) as values.
        """
        if type == 'AllNodes':
            node_ids = self.opcua_config['OPCUA_NODE_IDs']
        elif type == 'H2':
            node_ids = self.opcua_config['H2_FLOW_ID']
        else:
            logging.error("Invalid type '%s' provided. Must be 'AllNodes' or 'H2'.", type)
            raise ValueError('Wrong type for choosing the node IDs. Type must match "AllNodes" or "H2"!')

        values = {}
        for node_id in node_ids:
            try:
                node = self.client.get_node(node_id)  # Use the NodeID
                value = node.get_value()  # Read the value of the node
                values[node_id] = value
            except Exception as e:
                logging.error("Error reading node %s: %s", node_id, e)
                values[node_id] = None  # Return None for failed reads
        return values
 