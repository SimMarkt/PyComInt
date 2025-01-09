# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_data_trans.py: 
# > implements the data transfer from the Modbus client (PEMEL) and OPCUA (BM) to the SQL database 
# ----------------------------------------------------------------------------------------------------------------

import pg8000
from datetime import datetime 
from pci_connections import connect_modbus, connect_opc_ua, convert_bits, read_node_values  
########################################## import logging instead of prints  

def data_trans_func(modbus_connection, opcua_connection, sql_connection):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
        :param sql_connection: Object with SQL connection information
    """

    modbus_client = modbus_connection.client
    opcua_client = opcua_connection.client

    status_one_hot = modbus_client.read_pemel_status()
    pemel_values = modbus_client.read_process_values()
    opcua_values = opcua_client.read_node_values(type='AllNodes')   # The type defines the number of nodes to read, either all nodes 'AllNodes' or only the hydrogen flow rate 'H2' (for PEMEL control)
    
    # Write values into SQL database
    values = status_one_hot + pv_values + opcua_values
    if values is not None:
        sql_connection.insert_data(values)
    
    return print(f"Data transfer successfull!")