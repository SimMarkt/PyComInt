# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_data_trans.py: 
# > implements the data transfer from the Modbus client (PEMEL) and OPCUA (BM) to the SQL database 
# ----------------------------------------------------------------------------------------------------------------

import opcua
import pymodbus
import yaml

def data_func():
    return print(f"Control successfull!")