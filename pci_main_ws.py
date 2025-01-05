# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_main_ws.py: 
# > Main programming script that sets up a windows service performing data transfer between an OPCUA server, a Modbus client, and a SQL database
# > Application:    Power-to-Gas process with an proton exchange membrane electrolyzer (PEMEL) as Modbus client and a biological methanation unit (BM)
#                   with a programmable logic controller providing an OPCUA server
# 
# ----------------------------------------------------------------------------------------------------------------

import time
import threading
import win32serviceutil
import win32service
import win32event
import logging

from src.pci_el_control import el_control_func
from src.pci_data_trans import data_trans_func
from.src.pci_utils import load_config

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
            logging.info("Service is starting.")
            con_config = load_config()         # Load Modbus, OPCUA, and SQL configuration
            # Start the threaded tasks
            thread1s = threading.Thread(target=self.pemel_control(con_config))          # Thread with a 1s frequency, for PEMEL control
            thread10s = threading.Thread(target=self.data_store(con_config))            # Thread with a 10s frequency, for data storage 

            thread1s.start()
            thread10s.start()

            # Wait for the service to stop
            while self.running:
                time.sleep(1)

            # Wait for threads to finish
            thread1s.join()
            thread10s.join()

        except Exception as e:
            logging.error(f"Error during service execution: {e}")
            raise

    def pemel_control(self, con_config):
        """
            PEMEL control via OPCUA and Modbus
            :param modbus_config: Modbus configuration
            :param opcua_config: OPCUA server configuration
        """
        while self.running:
            el_control_func(con_config)
            time.sleep(1)

    def data_storage(self, con_config):
        """
            Data transfer via OPCUA and Modbus to SQL
            :param modbus_config: Modbus configuration
            :param opcua_config: OPCUA server configuration
            :param sql_config: SQL database configuration
        """
        while self.running:
            data_trans_func(con_config)
            time.sleep(10)

if __name__ == "__main__":
    print("PyComInt: Windows service for data transfer and PEMEL control")
    win32serviceutil.HandleCommandLine(PyComIntService)
