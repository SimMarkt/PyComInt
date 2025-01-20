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
        Contains the thread function for PEMEL control via OPCUA and Modbus
        :param control_interval: Interval for PEMEL control in [s]
    """
    while True:
        el_control_func(modbus_connection, opcua_connection)
        time.sleep(control_interval)

def el_control_func(modbus_connection, opcua_connection):
    """
        Controls PEMEL via OPCUA and Modbus
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
    """
    try:
        status_one_hot = modbus_connection.read_pemel_status()
        set_h2_flow = opcua_connection.read_node_values(type='H2')   # The type defines the number of nodes to read, either all nodes 'AllNodes' or only the hydrogen flow rate 'H2' (for PEMEL control)
        set_h2_flow = list(set_h2_flow.values()) # Extract the value from the dictionary

        if status_one_hot[10] == 1:                 # PEMEL operation is only valid if Hydrogen cooling temperature reached (BIT_10)    ##################### == 1
            modbus_connection.write_pemel_current(set_h2_flow[0])
            logging.info(f"PEMEL control successful: {set_h2_flow[0]} Nl/min")
        else:
            logging.warning(f"PEMEL control invalid: hydrogen cooling temperature is too high")

    except Exception as e:
        logging.error(f"Error in PEMEL control function: {e}")

def data_storage(storage_interval, modbus_connection, opcua_connection, sql_connection):
    """
        Contains the thread function for data transfer via OPCUA and Modbus to SQL
        :param storage_interval: Data storage interval in [s]
    """
    while True:
        data_trans_func(modbus_connection, opcua_connection, sql_connection)
        time.sleep(storage_interval)

def data_trans_func(modbus_connection, opcua_connection, sql_connection):
    """
        Transfers data via OPCUA and Modbus to SQL
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
        :param sql_connection: Object with SQL connection information
    """
    try:
        status_one_hot = modbus_connection.read_pemel_status()
        pemel_values = modbus_connection.read_pemel_process_values()
        opcua_values = opcua_connection.read_node_values(type='AllNodes')
        opcua_values = list(opcua_values.values()) # Extract the values from the dictionary

        # Write values into SQL database
        # values = status_one_hot + pemel_values + opcua_values     ####################################################################
        values = opcua_values                                       ####################################################################
        if values is not None:
            sql_connection.insert_data(values)

        logging.info("Data transfer successful.")
    except Exception as e:
        logging.error(f"Error in data transfer function: {e}")

def supervisor(reconnection_interval, modbus_connection, opcua_connection, sql_connection):
    """
        Attempts to reconnect to servers and clients upon connection failure. 
        :param reconnection_interval: Interval for reconnection
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
        :param sql_connection: Object with SQL connection information
    """
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




