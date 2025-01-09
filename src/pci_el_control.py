# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_el_control.py: 
# > implements the modbus connection to the PEMEL and converts the set value from a OPCUA node in the PLC of the BM to the Modbus client# 
# ----------------------------------------------------------------------------------------------------------------

from pci_connections import connect_modbus, connect_opc_ua, convert_bits, read_node_values  

def el_control_func(opcua_connection, modbus_connection):
    """
        PEMEL control via OPCUA and Modbus
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
    """
    
    modbus_client = modbus_connection.client
    opcua_client = opcua_connection.client

    status_one_hot = modbus_client.read_pemel_status()
    set_h2_flow = 

    # Connect to Modbus client
    modbus_config = con_config['modbus']
    modbus_client = connect_modbus(modbus_config)


          
    # Set up opcua connection
    opcua_config = con_config['opcua'] 
    opcua_client = connect_opc_ua()  # Connect to the server with user credentials
    if opcua_client:
        set_h2_flow = read_node_values(opcua_client, opcua_config['H2_FLOW_ID'])  # Read the value of the specified nodes  
    
    if status_one_hot[10] == 1: # PEMEL operation is only valid if Hydrogen cooling temperature reached (BIT_10)
            # Calculate PEMEL current set point according to the desired H2 flow rate
            set_current = convert_h2_flow_to_current(set_h2_flow, modbus_client)
            # Activate the specific bit
            write_result = modbus_client.write_register(modbus_config['WRITE_REGISTER'], set_current) # 15 A
            if write_result.isError():
                print(f"Error writing value {set_current} to register {modbus_config['WRITE_REGISTER']}")
            else:
                print(f"Successfully wrote {set_current} to register {modbus_config['WRITE_REGISTER']}")

    return print(f"PEMEL control successfull: {set_h2_flow} Nl/min -> {set_current} A")