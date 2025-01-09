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

def read_pemel_status(modbus_client, modbus_config)  :      
    """Read the Modbus register for PEMEL status _st"""
    response_st = modbus_client.read_holding_registers(modbus_config['PEMEL_STATUS']['ADDRESS'] - modbus_config['BASE_REGISTER_OFFSET'],
                                                        count=1,  # PEMEL status is located in one register
                                                        slave=modbus_config['SLAVE_ID'])  # Updated argument for slave ID

    if response_st.isError():
        print(f"Error reading PEMEL status - {modbus_config['PEMEL_STATUS']['ADDRESS']}: {response_st}")
        retries += 1
        if retries >= modbus_config['MAX_RETRIES']:
            print("Max retries reached, exiting.")
            break
    else:
        # Extract and display the value
        print(f"Read PEMEL status - {modbus_config['PEMEL_STATUS']['ADDRESS']}")
        status_one_hot = convert_bits(response_st.registers[0], modbus_config)
        retries = 0  # Reset retries on success)

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