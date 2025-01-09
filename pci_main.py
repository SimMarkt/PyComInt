# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface for chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_main.py: 
# > Main programming script that performs multi-threaded data transfer between an OPCUA server, a Modbus client, and a SQL database
# > Application: Power-to-Gas process with a proton exchange membrane electrolyzer (PEMEL) as a Modbus client, and a biological methanation unit (BM)
#                with a programmable logic controller (PLC) providing an OPC UA server.
# 
# ----------------------------------------------------------------------------------------------------------------

import time
import threading
import yaml
import logging

from src.pci_threads import pemel_control, data_storage, supervisor
from src.pci_modbus import ModbusConnection
from src.pci_opcua import OPCUAConnection
from src.pci_sql import SQLConnection

def setup_logging():
    """Set up logging to write messages to a file."""
    logging.basicConfig(
        filename='PyComInt.log',                                # Log file name
        level=logging.INFO,                                     # Log level
        format="%(asctime)s - %(levelname)s - %(message)s",     # Log format
        datefmt="%Y-%m-%d %H:%M:%S"                             # Date format
    )

def main(): 
    # Load general configuration
    try:
        with open("config/config_gen.yaml", "r") as env_file:
            gen_config = yaml.safe_load(env_file)
        logging.info("Loaded general configuration successfully.")
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return
    
    # Initialize connections    
    try:
        modbus_connection = ModbusConnection()
        opcua_connection = OPCUAConnection()
        sql_connection = SQLConnection()
        logging.info("Initialized all connections successfully.")
    except Exception as e:
        logging.error(f"Error initializing connections: {e}")
        return
 
    try:
        thread_con = threading.Thread(target=pemel_control(gen_config['PEMEL_CONTROL_INTERVAL'], modbus_connection, opcua_connection), daemon=True)      # Thread for PEMEL control
        thread_dat = threading.Thread(target=data_storage(gen_config['DATA_STORAGE_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for data storage
        thread_sup = threading.Thread(target=supervisor(gen_config['RECONNECTION_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for connection supervision
        
        thread_con.start()
        logging.info("PEMEL control thread started.")
        thread_dat.start()
        logging.info("Data storage thread started.")
        thread_sup.start()
        logging.info("Supervisor thread started.")
        
        while True:  # Keep the main thread running
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Exiting on user request (KeyboardInterrupt).")
    finally:
        # Clean up connections
        modbus_connection.client.close()
        opcua_connection.client.disconnect()
        sql_connection.close()
        logging.info("Connections closed successfully.")

if __name__ == "__main__":
    # Set up logging
    setup_logging()

    # Get the current timestamp
    logging.info("---------------------------------------------------------------------------------------------------------")
    logging.info(f"Starting PyComInt: Data transfer and PEMEL control in a Power-to-Gas process with biological methanation")

    # Run the main function
    main()
