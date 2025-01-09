# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface for chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_threads.py: 
# > Implements the different threads for PEMEL control, data storage, and thread supervision 
# ----------------------------------------------------------------------------------------------------------------

import time
import logging

def pemel_control(control_interval, modbus_connection, opcua_connection):
    """
        PEMEL control via OPCUA and Modbus
        :param control_interval: Interval for PEMEL control in [s]
    """
    while True:
        el_control_func(modbus_connection, opcua_connection)
        time.sleep(control_interval)

def el_control_func(opcua_connection, modbus_connection):
    """
        PEMEL control via OPCUA and Modbus
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
    """
    try:
        modbus_client = modbus_connection.client
        opcua_client = opcua_connection.client

        status_one_hot = modbus_client.read_pemel_status()
        set_h2_flow = opcua_client.read_node_values(type='H2')   # The type defines the number of nodes to read, either all nodes 'AllNodes' or only the hydrogen flow rate 'H2' (for PEMEL control)
        
        if status_one_hot[10] == 1:                 # PEMEL operation is only valid if Hydrogen cooling temperature reached (BIT_10)
            modbus_client.write_pemel_current(set_h2_flow)

        logging.info(f"PEMEL control successful: {set_h2_flow} Nl/min")
    except Exception as e:
        logging.error(f"Error in PEMEL control function: {e}")

def data_storage(storage_interval, modbus_connection, opcua_connection, sql_connection):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param storage_interval: Data storage interval in [s]
    """
    while True:
        data_trans_func(modbus_connection, opcua_connection, sql_connection)
        time.sleep(storage_interval)

def data_trans_func(modbus_connection, opcua_connection, sql_connection):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
        :param sql_connection: Object with SQL connection information
    """
    try:
        modbus_client = modbus_connection.client
        opcua_client = opcua_connection.client

        status_one_hot = modbus_client.read_pemel_status()
        pemel_values = modbus_client.read_process_values()
        opcua_values = opcua_client.read_node_values(type='AllNodes')

        # Write values into SQL database
        values = status_one_hot + pemel_values + opcua_values
        if values is not None:
            sql_connection.insert_data(values)

        logging.info("Data transfer successful.")
    except Exception as e:
        logging.error(f"Error in data transfer function: {e}")

def supervisor(reconnection_interval, modbus_connection, opcua_connection, sql_connection):
    while True:
        try:
            if not modbus_connection.is_connected():
                logging.warning("Reconnecting Modbus...")
                modbus_connection.connect()

            if not opcua_connection.is_connected():
                logging.warning("Reconnecting OPC UA...")
                opcua_connection.connect()

            if not sql_connection.is_connected():
                logging.warning("Reconnecting SQL...")
                sql_connection.connect()

            time.sleep(reconnection_interval)
        except Exception as e:
            logging.error(f"Error in supervisor function: {e}")




