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

from pci_el_control import el_control_func
from pci_data_trans import data_trans_func

def pemel_control():
    """PEMEL control via OPCUA and Modbus"""
    while True:
        el_control_func()
        time.sleep(1)

def data_storage():
    """Data transfer via OPCUA and Modbus to SQL"""
    while True:
        data_trans_func()
        time.sleep(10)

def main():   
    try:
        thread1s = threading.Thread(target=pemel_control, daemon=True)       # Thread with a 1s frequency, for PEMEL control
        thread10s = threading.Thread(target=data_storage, daemon=True)       # Thread with a 10s frequency, for data storage
        
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
