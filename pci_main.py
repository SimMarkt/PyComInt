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
import yaml
from src.pci_el_control import el_control_func
from src.pci_data_trans import data_trans_func
from.src.pci_connections import OPCUAConnection, ModbusConnection, SQLConnection

def pemel_control(control_interval, modbus_connection, opcua_connection):
    """
        PEMEL control via OPCUA and Modbus
        :param control_interval: Interval for PEMEL control in [s]
    """
    while True:
        el_control_func(modbus_connection, opcua_connection)
        time.sleep(control_interval)

def data_storage(storage_interval, modbus_connection, opcua_connection, sql_connection):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param storage_interval: Data storage interval in [s]
    """
    while True:
        data_trans_func(modbus_connection, opcua_connection, sql_connection)
        time.sleep(storage_interval)

def supervisor(reconnection_interval, modbus_connection, opcua_connection, sql_connection):
    while True:
        if not modbus_connection.is_connected():
            print("Reconnecting Modbus...")             #####################################################################
            modbus_connection.connect()
        
        if not opcua_connection.is_connected():
            print("Reconnecting OPC UA...")             #####################################################################
            opcua_connection.connect()

        if not sql_connection.is_connected():
            print("Reconnecting SQL...")                #####################################################################
            sql_connection.connect()

        time.sleep(reconnection_interval)  # Check every 10 seconds

def main(): 
    # Load general configuration
    with open("config/config_gen.yaml", "r") as env_file:
        gen_config = yaml.safe_load(env_file)
    
    # Initialize connections    
    modbus_connection = ModbusConnection()
    opcua_connection = OPCUAConnection()
    sql_connection = SQLConnection()
 
    try:
        thread_con = threading.Thread(target=pemel_control(gen_config['PEMEL_CONTROL_INTERVAL'], modbus_connection, opcua_connection), daemon=True)      # Thread for PEMEL control
        thread_dat = threading.Thread(target=data_storage(gen_config['DATA_STORAGE_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for data storage
        thread_sup = threading.Thread(target=supervisor(gen_config['RECONNECTION_INTERVAL'], modbus_connection, opcua_connection, sql_connection), daemon=True)        # Thread for connection supervision
        
        thread_con.start()
        thread_dat.start()
        thread_sup.start()
        
        while True:  # Keep the main thread running
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exiting on user request.")
    finally:
        print("Connections closed.")


if __name__ == "__main__":
    print("PyComInt: Script for data transfer and PEMEL control")
    main()
