# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_data_trans.py: 
# > implements the data transfer from the Modbus client (PEMEL) and OPCUA (BM) to the SQL database 
# ----------------------------------------------------------------------------------------------------------------

import pg8000
from datetime import datetime 
from pci_utils import connect_modbus, connect_opc_ua, read_node_values  
########################################## import logging instead of prints  

def convert_bits(value, modbus_config, bit_length=16):
    """
        Display a binary number, highlight which bits are active, and interpret their meanings based on a YAML config.
        Also returns a one-hot encoded array of the bits.
        :param value (int): The value read from the Modbus register.
        :param modbus_config (dict): A dictionary loaded from a YAML configuration file with bit interpretations.
        :bit_length (int): The length of the binary number (default is 16).
        :return status_one_hot (list): A one-hot encoded array representing the active/inactive state of each bit.
    """
    # # Convert the value to a binary string with leading zeros
    # binary_representation = f"{value:0{bit_length}b}"
    # print(f"Binary representation: {binary_representation}")
    # print("Bit positions:          " + " ".join(f"{i:>2}" for i in range(bit_length - 1, -1, -1)))

    status_config = modbus_config.get("PEMEL_STATUS", {})   # extract the bit interpretation
    one_hot = [0] * bit_length  # One-hot encoded array for the bit values

    print("PEMEL status:")
    for i in range(bit_length):
        bit_status = (value >> i) & 1  # Extract each bit
        one_hot[i] = bit_status       # Update the one-hot array

        # Get the bit description from the Modbus config
        bit_description = status_config.get(f"BIT_{i}", "Undefined")
        status = "Active" if bit_status else "Inactive"
        print(f"Bit {i}: {status} - {bit_description}")
    
    return one_hot

def read_pv(register, modbus_config):
    """
        Display and return the process values of the PEMEL.
        :param register: The Modbus register.
        :param modbus_config: A dictionary with Modbus configuration details.
        :return pv_values (list): Process values.
    """
    process_values = modbus_config.get("PROCESS_VALUES", {})
    count = process_values.get("COUNT")
    variable_names = [process_values.get(f"REG_{i}", f"Unknown_{i}") for i in range(count)]

    pv_values = []

    # Print and store the results
    print("Process Variable Values:")
    for i, value in enumerate(register):
        variable_name = variable_names[i]
        print(f"{variable_name}: {value}")
        pv_values.append(value)
    
    return pv_values 
    
def insert_data_into_db(values, sql_config):
    """
        Insert data into PostgreSQL database using pg8000
        :param values: measurement values to store in the SQL database
        :sql_config: SQL configuration data
    """
    try:
        # Get the current timestamp
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current date and time

        # Connect to PostgreSQL using pg8000
        conn = pg8000.connect(user=sql_config['DB_USER'], password=sql_config['DB_PASSWORD'], 
                              database=sql_config['DB_NAME'], host=sql_config['DB_HOST'], port=sql_config['DB_PORT'])
        cursor = conn.cursor()
        
        # Placeholders based on the number of values
        placeholders = ', '.join(['%s'] * (len(values) + 1))  # +1 for the timestamp
        query = f"INSERT INTO {sql_config['DB_TABLE']} {sql_config['DB_COLUMNS']} VALUES ({placeholders})"

        # Add the timestamp to the values
        values_with_timestamp = [current_timestamp] + values

        # Execute the query
        cursor.execute(query, values_with_timestamp)

        # Commit the transaction
        conn.commit()
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("Data inserted successfully into the PostgreSQL database.")
    except Exception as e:
        print(f"Error inserting data into PostgreSQL: {e}")

def data_trans_func(con_config):
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
        
        # Read the Modbus registers for PEMEL process values "_pv"
        response_pv = modbus_client.read_holding_registers(modbus_config['PROCESS_VALUES']['ADDRESS'] - modbus_config['BASE_REGISTER_OFFSET'],
                                                           count=modbus_config['PROCESS_VALUES']['COUNT'],  # Read all important registers
                                                           slave=modbus_config['SLAVE_ID'])  # Updated argument for slave ID

        if response_pv.isError():
            print(f"Error reading PEMEL process values - {modbus_config['PROCESS_VALUES']['ADDRESS']}...: {response_pv}")
            retries += 1
            if retries >= modbus_config['MAX_RETRIES']:
                print("Max retries reached, exiting.")
                break
        else:
            # Extract and display the value
            print(f"Read PEMEL process values - {modbus_config['PROCESS_VALUES']['ADDRESS']}...")
            pv_values = read_pv(response_pv, modbus_config)
            retries = 0  # Reset retries on success

    # Set up opcua connection
    opcua_config = con_config['opcua'] 
    opcua_client = connect_opc_ua()  # Connect to the server with user credentials
    if opcua_client:
        opcua_values = read_node_values(opcua_client, opcua_config['OPCUA_NODE_IDs'])  # Read the value of the specified nodes
    
    # Write values into SQL database
    sql_config = con_config['sql']
    values = status_one_hot + pv_values + opcua_values
    if values is not None:
        insert_data_into_db(values, sql_config)  # Insert the value and timestamp into PostgreSQL

    modbus_client.close() 
    opcua_client.disconnect()  
    print("Disconnected.")
    return print(f"Data transfer successfull!")