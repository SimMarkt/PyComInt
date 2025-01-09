# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_el_control.py: 
# > implements the modbus connection to the PEMEL and converts the set value from a OPCUA node in the PLC of the BM to the Modbus client# 
# ----------------------------------------------------------------------------------------------------------------

from pci_utils import connect_modbus, connect_opc_ua, read_node_values  

def el_control_func(con_config):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param con_config: Contains information about the configuration details of the communication
    """
    
    # Connect to Modbus client
    modbus_config = con_config['modbus']
    modbus_client = connect_modbus(modbus_config)

    # Set up opcua connection
    opcua_config = con_config['opcua'] 
    opcua_client = connect_opc_ua()  # Connect to the server with user credentials
    if opcua_client:
        opcua_values = read_node_values(opcua_client, opcua_config['OPCUA_NODE_IDs'])  # Read the value of the specified nodes

    return print(f"PEMEL control successfull: {h2_flow_rate} Nl/min -> {el_current} A")