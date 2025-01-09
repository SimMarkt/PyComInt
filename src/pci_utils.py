# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_utils.py: 
# > provides utility functions 
# ----------------------------------------------------------------------------------------------------------------

import yaml
from opcua import Client
from pymodbus.client import ModbusTcpClient

def load_config():
    # load Modbus configuration
    with open("config/config_modbus.yaml", "r") as env_file:
            modbus_config = yaml.safe_load(env_file)

    # load OPCUA configuration
    with open("config/config_opcua.yaml", "r") as env_file:
            opcua_config = yaml.safe_load(env_file)

    # load SQL configuration
    with open("config/config_sql.yaml", "r") as env_file:
            sql_config = yaml.safe_load(env_file)

    con_config = {'modbus': modbus_config, 'opcua': opcua_config, 'sql': sql_config}   

    return con_config

def connect_modbus(modbus_config):
    """Connect to Modbus client with authentication"""
    modbus_client = ModbusTcpClient(modbus_config['IP_ADDRESS'], port=modbus_config['PORT'])
    if not modbus_client.connect():
        print("Unable to connect to Modbus server.")
        return
    print(f"Connected to Modbus server at {modbus_config['IP_ADDRESS']}:{modbus_config['PORT']}")
    return modbus_client

def connect_opc_ua(opcua_config):
    """Connect to OPC UA server with authentication"""
    client = Client(opcua_config['URL'])
    try:
        # Set user credentials directly
        client.set_user(opcua_config['USERNAME'])
        client.set_password(opcua_config['PASSWORD'])

        client.connect()
        print(f"Connected to {opcua_config['URL']} as {opcua_config['USERNAME']}")
        return client
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None
    
def convert_bits(value, modbus_config, bit_length=16):
    """
        Display a binary number, highlight which bits are active, and interpret their meanings based on a YAML config.
        Also returns a one-hot encoded array of the bits.
        :param value (int): The value read from the Modbus register.
        :param modbus_config (dict): A dictionary loaded from a YAML configuration file with bit interpretations.
        :bit_length (int): The length of the binary number (default is 16).
        :return status_one_hot (list): A one-hot encoded array representing the active/inactive state of each bit.
    """
    # # Convert the value to a binary string with leading zeros
    # binary_representation = f"{value:0{bit_length}b}"
    # print(f"Binary representation: {binary_representation}")
    # print("Bit positions:          " + " ".join(f"{i:>2}" for i in range(bit_length - 1, -1, -1)))

    status_config = modbus_config.get("PEMEL_STATUS", {})   # extract the bit interpretation
    one_hot = [0] * bit_length  # One-hot encoded array for the bit values

    print("PEMEL status:")
    for i in range(bit_length):
        bit_status = (value >> i) & 1  # Extract each bit
        one_hot[i] = bit_status       # Update the one-hot array

        # Get the bit description from the Modbus config
        bit_description = status_config.get(f"BIT_{i}", "Undefined")
        status = "Active" if bit_status else "Inactive"
        print(f"Bit {i}: {status} - {bit_description}")
    
    return one_hot

def read_node_values(client, node_ids):
    """
        Read the values of multiple nodes using their NodeIDs.
        :param client: OPC UA client object.
        :param node_ids: list of Node IDs to read values from.
        :return values: dictionary with node IDs as keys and their corresponding values (or errors) as values.
    """
    values = {}
    for node_id in node_ids:
        try:
            node = client.get_node(node_id)  # Use the NodeID
            value = node.get_value()  # Read the value of the node
            values[node_id] = value
        except Exception as e:
            print(f"Error reading node {node_id}: {e}")
            values[node_id] = None  # Return None for failed reads
    return values