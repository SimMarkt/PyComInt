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
from pci_utils import load_config       

def connect_opc_ua(opcua_config):
    """Connect to OPC UA server with authentication"""
    client = Client(opcua_config['URL'])
    try:
        # Set user credentials directly
        client.set_user(opcua_config['USERNAME'])
        client.set_password(opcua_config['PASSWORD'])

        client.connect()
        print(f"Connected to {opcua_config['URL']} as {opcua_config['USERNAME']}")
        return client
    except Exception as e:
        print(f"Error connecting to server: {e}")
        return None
    
def read_node_value(client, node_id):
    """Read the value of a node using its NodeID"""
    try:
        node = client.get_node(node_id)  # Use the NodeID
        value = node.get_value()  # Read the value of the node
        # print(f"Value of node {node_id}: {value}")
        return value
    except Exception as e:
        print(f"Error reading node {node_id}: {e}")
        return None
    
def insert_data_into_db(values, sql_config):
    """Insert data into PostgreSQL database using pg8000"""
    try:
        # Get the current timestamp
        current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current date and time

        # Connect to PostgreSQL using pg8000
        conn = pg8000.connect(user=sql_config['DB_USER'], password=sql_config['DB_PASSWORD'], 
                              database=sql_config['DB_NAME'], host=sql_config['DB_HOST'], port=sql_config['DB_PORT'])
        cursor = conn.cursor()
        
        # Create an INSERT query with timestamp and real_Ph value
        query = "INSERT INTO " + sql_config['DB_TABLE'] + " " + sql_config['DB_COLUMNS'] + " VALUES (%s, %s)" ############## ADJUST NUMBER OF VALUES TO (%s,...)
        cursor.execute(query, (current_timestamp, values))  # Insert the values 

        # Commit the transaction
        conn.commit()
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("Data inserted successfully into the PostgreSQL database.")
    except Exception as e:
        print(f"Error inserting data into PostgreSQL: {e}")


def data_trans_func():
    """Data transfer via OPCUA and Modbus to SQL"""
    modbus_config, opcua_config, sql_config = load_config()


    opcua_config['str_inv']
    return print(f"Data transfer successfull!")