# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface of chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_utils.py: 
# > provides utility functions 
# ----------------------------------------------------------------------------------------------------------------

import time
import yaml
from datetime import datetime 
from opcua import Client
from pymodbus.client import ModbusTcpClient
import pg8000
import logging

class ModbusConnection:
    def __init__(self):
       # Load Modbus configuration
        with open("config/config_modbus.yaml", "r") as env_file:
            self.modbus_config = yaml.safe_load(env_file)
        self.client = None
        self.connected = False

    def connect(self):
        """
            Establish the connection to the Modbus server. (Uses several attempts, since the Modbus connection is deemed less reliable)
        """
        for attempt in range(self.modbus_config['MAX_RETRIES']):
            try:
                self.client = ModbusTcpClient(self.modbus_config['IP_ADDRESS'], port=self.modbus_config['PORT'])
                self.connected = self.client.connect()
                if self.connected:
                    print(f"Successfully connected to Modbus server at {self.modbus_config['IP_ADDRESS']}:{self.modbus_config['PORT']}")
                    return
            except Exception as e:
                print(f"Attempt {attempt + 1}/{self.modbus_config['MAX_RETRIES']} - Modbus connection failed: {e}")
            time.sleep(self.modbus_config['RETRY_INTERVAL'])
        print(f"Failed to connect to Modbus server after {self.modbus_config['MAX_RETRIES']} attempts.")
        self.connected = False

    def is_connected(self):
        """
            Check if the Modbus connection is active.
            :return: True if connected, False otherwise.
        """
        return self.connected and self.client and self.client.is_socket_open()
    
    def read_pemel_status(self):
        """
            Read the Modbus register for PEMEL status with retry logic
            :return: One-hot-encoded array with status signals if the reading was successfull or None if not
        """
        max_retries = self.modbus_config['MAX_RETRIES']
        retries = 0
        while retries < max_retries:
            try:
                # Read the Modbus register for PEMEL status
                response = self.client.read_holding_registers(self.modbus_config['PEMEL_STATUS']['ADDRESS'] - self.modbus_config['BASE_REGISTER_OFFSET'],
                                                            count=1,  # PEMEL status is located in one register
                                                            slave=self.modbus_config['SLAVE_ID'])  # Updated argument for slave ID
                if response.isError():
                    retries += 1
                    raise Exception(f"Error reading PEMEL status - {self.modbus_config['PEMEL_STATUS']['ADDRESS']}: {response}")

                print(f"Read PEMEL status - {self.modbus_config['PEMEL_STATUS']['ADDRESS']}")
                status_one_hot = self.convert_bits(response.registers[0])
                return status_one_hot  # Return processed data if successful
            except Exception as e:
                print(f"Reading the PEMEL status register failed: {e}")
                retries += 1
                time.sleep(self.modbus_config['RETRY_INTERVAL'])
        
        return None  # Return None if all retries failed
    
    def read_pemel_process_values(self):
        """
            Read the Modbus registers for PEMEL process values with retry logic
            :return: Array with process values if the reading was successfull or None if not
        """
        max_retries = self.modbus_config['MAX_RETRIES']
        retries = 0
        while retries < max_retries:
            try:
                # Read the Modbus register for PEMEL status
                response = self.client.read_holding_registers(self.modbus_config['PROCESS_VALUES']['ADDRESS'] - self.modbus_config['BASE_REGISTER_OFFSET'],
                                                              count=self.modbus_config['PROCESS_VALUES']['COUNT'],  # Read all important registers
                                                              slave=self.modbus_config['SLAVE_ID'])  # Updated argument for slave ID
                if response.isError():
                    retries += 1
                    raise Exception(f"Error reading PEMEL process values - {self.modbus_config['PROCESS_VALUES']['ADDRESS']}: {response}")

                print(f"Read PEMEL process values - {self.modbus_config['PROCESS_VALUES']['ADDRESS']}...")
                pv_values = self.convert_process_values(response)
                return pv_values  # Return processed data if successfull
            except Exception as e:
                print(f"Reading the PEMEL process values registers failed: {e}")
                retries += 1
                time.sleep(self.modbus_config['RETRY_INTERVAL'])
        
        return None  # Return None if all retries failed
    
    def convert_bits(self, value, bit_length=16):
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

        status_config = self.modbus_config.get("PEMEL_STATUS", {})   # extract the bit interpretation
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
    
    def convert_process_values(self, register):
        """
            (Display and) return the process values of the PEMEL.
            :param register: The Modbus register.
            :return pv_values: Process values in an array.
        """
        process_values = self.modbus_config.get("PROCESS_VALUES", {})
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

class OPCUAConnection:
    def __init__(self):
        # Load OPCUA configuration
        with open("config/config_opcua.yaml", "r") as env_file:
                self.opcua_config = yaml.safe_load(env_file)
        self.client = None

    def connect(self):
        """
        Establish the connection to the OPCUA server.
        """
        try:
            self.client = Client(self.opcua_config['URL'])
            # Set user credentials directly
            self.client.set_user(self.opcua_config['USERNAME'])
            self.client.set_password(self.opcua_config['PASSWORD'])

            self.client.connect()
            print(f"Connected to {self.opcua_config['URL']} as {self.opcua_config['USERNAME']}")
        except Exception as e:
            print(f"OPC UA connection failed: {e}")
            self.client = None  # Mark as unavailable

    def is_connected(self):
        """
        Check if the OPCUA connection is active.
        :return: True if connected, False otherwise.
        """
        return self.client is not None
        
    def read_node_values(self, type='AllNodes'):
        """
            Read the values of multiple nodes using their NodeIDs.
            :param type: Reading type > either 'AllNodes' for reading all OPCUA nodes or 'H2' for reading only the hydrogen volume flow rate (for PEMEL control)
            :return values: Dictionary with node IDs as keys and their corresponding values (or errors) as values.
        """
        if type == 'AllNodes':
            node_ids = self.opcua_config['OPCUA_NODE_IDs']
        elif type == 'H2':
            node_ids = self.opcua_config['H2_FLOW_ID']
        else:
            assert False, 'Wrong type for choosing the nodeIDs, type need to match "AllNodes" or "H2"!'

        values = {}
        for node_id in node_ids:
            try:
                node = self.client.get_node(node_id)  # Use the NodeID
                value = node.get_value()  # Read the value of the node
                values[node_id] = value
            except Exception as e:
                print(f"Error reading node {node_id}: {e}")
                values[node_id] = None  # Return None for failed reads
        return values
    
    def interpolate_h2_flow(self, current_array, h2_flowrate_array, set_h2_flow):
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
        
    def convert_h2_flow_to_current(self, set_h2_flow):
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
    
class SQLConnection:
    def __init__(self):
        # Load SQL configuration
        with open("config/config_sql.yaml", "r") as env_file:
            self.sql_config = yaml.safe_load(env_file)
        self.connection = None

    def connect(self):
        """
        Establish the connection to the OPCUA server.
        """
        try:
            # Connect to PostgreSQL using pg8000
            self.connection = pg8000.connect(user=self.sql_config['DB_USER'], 
                                             password=self.sql_config['DB_PASSWORD'],
                                             database=self.sql_config['DB_NAME'], 
                                             host=self.sql_config['DB_HOST'], 
                                             port=self.sql_config['DB_PORT'])
            print(f"Connected to {self.sql_config['DB_NAME']} as {self.sql_config['DB_USER'],}")   
            return
        except Exception as e:
            print(f"SQL connection failed: {e}")                                                   
            self.connection = None  # Mark as unavailable

    def is_connected(self):
        """
        Check if the SQL connection is active.
        :return: True if connected, False otherwise.
        """
        return self.connection is not None
    
    def insert_data(self, values):
        """
            Insert data into PostgreSQL database using pg8000
            :param values: measurement values to store in the SQL database
        """
        try:
            # Get the current timestamp
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current date and time
            cursor = self.connection.cursor()
            
            # Placeholders based on the number of values
            placeholders = ', '.join(['%s'] * (len(values) + 1))  # +1 for the timestamp
            query = f"INSERT INTO {self.sql_config['DB_TABLE']} {self.sql_config['DB_COLUMNS']} VALUES ({placeholders})"

            # Add the timestamp to the values
            values_with_timestamp = [current_timestamp] + values

            # Execute the query
            cursor.execute(query, values_with_timestamp)

            # Commit the transaction
            self.connection.commit()
            
            # Close the cursor
            cursor.close()
            print("Data inserted successfully into the PostgreSQL database.") 
        except Exception as e:
            print(f"Error inserting data into PostgreSQL: {e}")
        

    


