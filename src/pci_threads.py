"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

pci_threads.py:
> Implements the different threads for PEMEL control, data storage, and thread supervision
----------------------------------------------------------------------------------------------------
"""

# pylint: disable=no-member, broad-exception-caught, broad-exception-raised

import time
import logging

def pemel_control(control_interval, modbus_connection, opcua_connection):
    """
        Contains the thread function for PEMEL control via OPCUA and Modbus
        :param control_interval: Interval for PEMEL control in [s]
    """

    last_log_time = 0  # Initialize last log time for PEMEL control

    while True:
        # Call the PEMEL control function and pass the last log time
        last_log_time = el_control_func(modbus_connection, opcua_connection, last_log_time)
        time.sleep(control_interval)

def el_control_func(modbus_connection, opcua_connection, last_log_time):
    """
        Controls PEMEL via OPCUA and Modbus
        :param opcua_connection: Object with OPCUA connection information
        :param modbus_connection: Object with Modbus connection information
        :param last_log_time: Timestamp of the last log message
        :return: Updated timestamp of the last log message
    """
    try:
        status_one_hot = modbus_connection.read_pemel_status()
        set_h2_flow = opcua_connection.read_node_values(type='H2')   # The type defines the number of nodes to read, either all nodes 'AllNodes' or only the hydrogen flow rate 'H2' (for PEMEL control)
        set_h2_flow = list(set_h2_flow.values()) # Extract the value from the dictionary

        current_time = time.time()  # Get the current time

        if status_one_hot[10] == 1:                 # PEMEL operation is only valid if Hydrogen cooling temperature reached (BIT_10) 
            modbus_connection.write_pemel_current(set_h2_flow[0])
            # Log only if 10 seconds have passed
            if current_time - last_log_time >= 10:
                # logging.info(f"PEMEL control successful: {set_h2_flow[0]} Nl/min")
                last_log_time = current_time  # Update the last log time
        else:
            # Log only if 10 seconds have passed
            if current_time - last_log_time >= 10:
                logging.warning("PEMEL control invalid: hydrogen cooling temperature is too high")
                last_log_time = current_time  # Update the last log time

    except Exception as e:
        logging.error("Error in PEMEL control function: %s", e)
    
    # Return the updated last log time
    return last_log_time

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
        values = opcua_values + status_one_hot + pemel_values
        if values is not None:
            sql_connection.insert_data(values)

        # logging.info("Data transfer successful.")
    except Exception as e:
        logging.error("Error in data transfer function: %s", e)

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
            logging.error("Error in supervisor function: %s", e)




