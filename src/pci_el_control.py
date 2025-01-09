# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_el_control.py: 
# > implements the modbus connection to the PEMEL and converts the set value from a OPCUA node in the PLC of the BM to the Modbus client# 
# ----------------------------------------------------------------------------------------------------------------

from pci_utils import connect_modbus, connect_opc_ua, convert_bits, read_node_values  

def interpolate_h2_flow(current_array, h2_flowrate_array, set_h2_flow, modbus_client):
    """
    Interpolate H2 flow rate to determine the current based on the given value.
    :param array: List of H2 flow values
    :param set_value: Input H2 flow value to interpolate
    :return: Interpolated current value
    """
    if set_h2_flow >= max(h2_flowrate_array):               # If the input exceeds the maximum array value
        return modbus_client['MAX_CURRENT']
    if set_h2_flow < modbus_client['MIN_CURRENT']:    # If the input is below the minimum electrical current
        return 0
    
    for i in range(len(h2_flowrate_array) - 1):
        if h2_flowrate_array[i] <= set_h2_flow <= h2_flowrate_array[i + 1] or h2_flowrate_array[i] >= set_h2_flow >= h2_flowrate_array[i + 1]:
            # Linear interpolation
            slope = (current_array[i + 1] - current_array[i]) / (h2_flowrate_array[i + 1] - h2_flowrate_array[i])
            current_value = current_array[i] + slope * (set_h2_flow - h2_flowrate_array[i])
            return round(current_value)
    
def convert_h2_flow_to_current(set_h2_flow, modbus_client):
    """
    Convert H2 flow rate to current by reading from a file and interpolating.
    :param set_value: Input H2 flow value
    :return: Converted current value
    """
    try:
        with open(modbus_client['H2_FLOW_ARRAY'], "r") as fptr:
            # Skip the header and read the data
            lines = fptr.readlines()
            header = lines[0].strip()  # Read the header
            data = [line.strip().split(';') for line in lines[1:]]  # Read and split data
            
            # Parsing the data into lists
            current_array = [int(row[0]) for row in data]
            h2_flowrate_array = [float(row[1]) for row in data]

        set_current = interpolate_h2_flow(current_array, h2_flowrate_array, set_h2_flow, modbus_client)  # Interpolate H2 flow to current
    except Exception as e:
        print(f"Error occurred while processing the file: {e}")
    return set_current

def el_control_func(con_config):
    """
        Data transfer via OPCUA and Modbus to SQL
        :param con_config: Contains information about the configuration details of the communication
    """
    
    # Connect to Modbus client
    modbus_config = con_config['modbus']
    modbus_client = connect_modbus(modbus_config)

    retries = 0     # counts the number of failed readings
    while True:
        # Read the Modbus register for PEMEL status "_st"
        response_st = modbus_client.read_holding_registers(modbus_config['PEMEL_STATUS']['ADDRESS'] - modbus_config['BASE_REGISTER_OFFSET'],
                                                           count=1,  # PEMEL status is located in one register
                                                           slave=modbus_config['SLAVE_ID'])  # Updated argument for slave ID

        if response_st.isError():
            print(f"Error reading PEMEL status - {modbus_config['PEMEL_STATUS']['ADDRESS']}: {response_st}")
            retries += 1
            if retries >= modbus_config['MAX_RETRIES']:
                print("Max retries reached, exiting.")
                break
        else:
            # Extract and display the value
            print(f"Read PEMEL status - {modbus_config['PEMEL_STATUS']['ADDRESS']}")
            status_one_hot = convert_bits(response_st.registers[0], modbus_config)
            retries = 0  # Reset retries on success
          
    # Set up opcua connection
    opcua_config = con_config['opcua'] 
    opcua_client = connect_opc_ua()  # Connect to the server with user credentials
    if opcua_client:
        set_h2_flow = read_node_values(opcua_client, opcua_config['H2_FLOW_ID'])  # Read the value of the specified nodes  
    
    if status_one_hot[10] == 1: # PEMEL operation is only valid if Hydrogen cooling temperature reached (BIT_10)
            # Calculate PEMEL current set point according to the desired H2 flow rate
            set_current = convert_h2_flow_to_current(set_h2_flow, modbus_client)
            # Activate the specific bit
            write_result = modbus_client.write_register(modbus_config['WRITE_REGISTER'], set_current) # 15 A
            if write_result.isError():
                print(f"Error writing value {set_current} to register {0x8000}")
            else:
                print(f"Successfully wrote {set_current} to register {0x8000}")

    return print(f"PEMEL control successfull: {h2_flow_rate} Nl/min -> {el_current} A")