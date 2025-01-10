# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface for chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_main_ws.py: 
# > Main programming script that sets up a windows service performing data transfer between an OPCUA server, a Modbus client, and a SQL database
# > Application: Power-to-Gas process with a proton exchange membrane electrolyzer (PEMEL) as a Modbus client, and a biological methanation unit (BM)
#                with a programmable logic controller (PLC) providing an OPC UA server.
# 
# ----------------------------------------------------------------------------------------------------------------

import time
import threading
import win32serviceutil
import win32service
import win32event
import yaml
import logging

from src.pci_threads import pemel_control, data_storage, supervisor
from src.pci_modbus import ModbusConnection
from src.pci_opcua import OPCUAConnection
from src.pci_sql import SQLConnection

def setup_logging():
    """Sets up logging to write messages to a file."""
    logging.basicConfig(
        filename='PyComInt.log',                                # Log file name
        level=logging.INFO,                                     # Log level
        format="%(asctime)s - %(levelname)s - %(message)s",     # Log format
        datefmt="%Y-%m-%d %H:%M:%S"                             # Date format
    )

class PyComIntService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ThreadedPyComIntService"
    _svc_display_name_ = "Threaded Python Windows Service for chemical plant communication"
    _svc_description_ = "A Python Windows Service that prints connects an OPCUA, a Modbus client, and a SQL database using multi-threading for different data transfer frequencies."

    def __init__(self, args):
        try:
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self.running = True
            logging.info("Service initialized.")
        except Exception as e:
            logging.error(f"Error during service initialization: {e}")
            raise

    def SvcStop(self):
        # Stop the service
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        try:
            # Load general configuration
            with open("config/config_gen.yaml", "r") as env_file:
                gen_config = yaml.safe_load(env_file)
            
            # Initialize connections    
            modbus_connection = ModbusConnection()
            opcua_connection = OPCUAConnection()
            sql_connection = SQLConnection()

            logging.info("Service is starting.")
            thread_con = threading.Thread(target=pemel_control(gen_config['PEMEL_CONTROL_INTERVAL'], modbus_connection, opcua_connection), daemon=True)      # Thread for PEMEL control
            thread_dat = threading.Thread(target=data_storage(gen_config['DATA_STORAGE_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for data storage
            thread_sup = threading.Thread(target=supervisor(gen_config['RECONNECTION_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for connection supervision
         
            thread_con.start()
            thread_dat.start()
            thread_sup.start()

            # Wait for the service to stop
            while self.running:
                time.sleep(1)

            # Wait for threads to finish
            thread_con.join()
            thread_dat.join()
            thread_sup.join()

        except Exception as e:
            logging.error(f"Error during service execution: {e}")
            raise

if __name__ == "__main__":
    # Set up logging
    setup_logging()

    # Get the current timestamp
    logging.info("------------------------------------------------------------------------------------------------------------------------------")
    logging.info(f"Starting PyComInt as a windows service: Data transfer and PEMEL control in a Power-to-Gas process with biological methanation")

    # Run the windows service
    win32serviceutil.HandleCommandLine(PyComIntService)
