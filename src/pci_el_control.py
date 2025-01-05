# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_el_control.py: 
# > implements the modbus connection to the PEMEL and converts the set value from a OPCUA node in the PLC of the BM to the Modbus client# 
# ----------------------------------------------------------------------------------------------------------------

import opcua
import pymodbus
import yaml

def el_control_func():
    h2_flow_rate = 10
    el_current = 2
    return print(f"PEMEL control successfull: {h2_flow_rate} Nl/min -> {el_current} A")