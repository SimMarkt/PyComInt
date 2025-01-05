# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_utils.py: 
# > provides utility functions 
# ----------------------------------------------------------------------------------------------------------------

import yaml

def load_config():
    # load Modbus configuration
    with open("config/config_modbus.yaml", "r") as env_file:
            modbus_config = yaml.safe_load(env_file)

    # load OPCUA configuration
    with open("config/config_opcua.yaml", "r") as env_file:
            opcua_config = yaml.safe_load(env_file)

    # load SQL configuration
    with open("config/config_sql.yaml", "r") as env_file:
            sql_config = yaml.safe_load(env_file)
       
    return modbus_config, opcua_config, sql_config