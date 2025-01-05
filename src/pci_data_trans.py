# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_data_trans.py: 
# > implements the data transfer from the Modbus client (PEMEL) and OPCUA (BM) to the SQL database 
# ----------------------------------------------------------------------------------------------------------------

import yaml
import pg8000
from opcua import Client
from pymodbus.client import ModbusTcpClient
from datetime import datetime 
from pci_utils import connect_opc_ua, read_node_values  
########################################## import logging instead of prints  

def convert_bits(value, bit_length=16):
    """Display a binary number and highlight which bits are active."""
    binary_representation = f"{value:0{bit_length}b}"  # Convert to binary with leading zeros
    print(f"Binary representation: {binary_representation}")
    print("Bit positions:          " + " ".join(f"{i:>2}" for i in range(bit_length - 1, -1, -1)))
    
    for i in range(bit_length):
        bit_status = (value >> i) & 1  # Extract each bit
        print(f"Bit {i}: {'Active' if bit_status else 'Inactive'}")  
    
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
    """Data transfer via OPCUA and Modbus to SQL"""

    # Set up modbus connection
    modbus_config = con_config['modbus']
    modbus_client = ModbusTcpClient(modbus_config['IP_ADDRESS'], port=modbus_config['PORT'])
    if not modbus_client.connect():
        print("Unable to connect to Modbus server.")
        return
    print(f"Connected to Modbus server at {modbus_config['IP_ADDRESS']}:{modbus_config['PORT']}")

    retries = 0     # counts the number of failed readings
    while True:
        # Read the Modbus register for PEMEL status
        response = modbus_client.read_holding_registers(modbus_config['PEMEL_STATUS']['ADDRESS'] - modbus_config['BASE_REGISTER_OFFSET'],
                                                         count=1,  # PEMEL status is located in one register
                                                         slave=modbus_config['SLAVE_ID'])  # Updated argument for slave ID

        if response.isError():
            print(f"Error reading 0x8060: {response}")
            retries += 1
            if retries >= modbus_config['MAX_RETRIES']:
                print("Max retries reached, exiting.")
                break
        else:
            # Extract and display the value
            print(f"Read PEMEL status - {modbus_config['PEMEL_STATUS']['ADDRESS']}")
            convert_bits(response.registers[0])
            retries = 0  # Reset retries on success
        
        response2 = client.read_holding_registers(0x8060 - BASE_REGISTER_OFFSET,
                                                    count=1,  # Read a single register
                                                    slave=SLAVE_ID)  # Updated argument for slave ID

        if response2.isError():
            print(f"Error reading 0x8060: {response2}")
            retries += 1
            if retries >= MAX_RETRIES:
                print("Max retries reached, exiting.")
                break
        else:
            # Extract and display the value
            print("0x8060")
            display_bits(response2.registers[0])
            retries = 0  # Reset retries on success





    # Set up opcua connection
    opcua_config = con_config['opcua'] 
    opcua_client = connect_opc_ua()  # Connect to the server with user credentials
    if opcua_client:
        opcua_values = read_node_values(opcua_client, opcua_config['OPCUA_NODE_IDs'])  # Read the value of the specified node
    
    # Write values into SQL database
    sql_config = con_config['sql']
    values = modbus_values + opcua_values
    if values is not None:
        insert_data_into_db(values, sql_config)  # Insert the value and timestamp into PostgreSQL

    modbus_client.close() 
    opcua_client.disconnect()  
    print("Disconnected.")
    return print(f"Data transfer successfull!")