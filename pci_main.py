# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_main.py: 
# > Main programming script that performs data transfer between an OPCUA server, a Modbus client, and a SQL database
# > Application:    Power-to-Gas process with an proton exchange membrane electrolyzer (PEMEL) as Modbus client and a biological methanation unit (BM)
#                   with a programmable logic controller providing an OPCUA server
# 
# ----------------------------------------------------------------------------------------------------------------

import time
import threading

from src.pci_el_control import el_control_func
from src.pci_data_trans import data_trans_func
from.src.pci_utils import load_config

def pemel_control(con_config):
    """
        PEMEL control via OPCUA and Modbus
        :param con_config: Modbus, OPCUA, and SQL configuration
    """
    while True:
        el_control_func(con_config)
        time.sleep(1)

def data_storage(con_config):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param con_config: Modbus, OPCUA, and SQL configuration
    """
    while True:
        data_trans_func(con_config)
        time.sleep(10)

def supervisor(opcua_connection, modbus_connection, sql_connection):
    while True:
        if not opcua_connection.is_connected():
            print("Reconnecting OPC UA...")
            opcua_connection.connect()

        if not modbus_connection.is_connected():
            print("Reconnecting Modbus...")
            modbus_connection.connect()

        if not sql_connection.is_connected():
            print("Reconnecting SQL...")
            sql_connection.connect()

        time.sleep(10)  # Check every 10 seconds

def main():   
    try:
        con_config = load_config()         # Load Modbus, OPCUA, and SQL configuration
        thread1s = threading.Thread(target=pemel_control(con_config), daemon=True)       # Thread with a 1s frequency, for PEMEL control
        thread10s = threading.Thread(target=data_storage(con_config), daemon=True)       # Thread with a 10s frequency, for data storage
        
        thread1s.start()
        thread10s.start()
        
        while True:  # Keep the main thread running
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting on user request.")
    finally:
        print("Connections closed.")


if __name__ == "__main__":
    print("PyComInt: Script for data transfer and PEMEL control")
    main()
