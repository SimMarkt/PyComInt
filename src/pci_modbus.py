# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface for chemical plants
# https://github.com/SimMarkt/PyComInt

# pci_modbus.py: 
# > Implements the Modbus connection
# ----------------------------------------------------------------------------------------------------------------

import time
import yaml
from pymodbus.client import ModbusTcpClient
import logging

class ModbusConnection:
    def __init__(self):
        try:
            # Load Modbus configuration
            with open("config/config_modbus.yaml", "r") as env_file:
                self.modbus_config = yaml.safe_load(env_file)
            self.client = None
            self.connected = False
        except Exception as e:
            logging.error(f"Failed to load Modbus configuration: {e}")

    def connect(self):
        """
            Establish the connection to the Modbus server. (Uses several attempts, since the Modbus connection is deemed less reliable)
        """
        for attempt in range(self.modbus_config['MAX_RETRIES']):
            try:
                self.client = ModbusTcpClient(self.modbus_config['IP_ADDRESS'], port=self.modbus_config['PORT'])
                self.connected = self.client.connect()
                if self.connected:
                    logging.info(f"Connected to Modbus server at {self.modbus_config['IP_ADDRESS']}:{self.modbus_config['PORT']}")
                    return
            except Exception as e:
                logging.warning(f"Attempt {attempt + 1}/{self.modbus_config['MAX_RETRIES']} - Modbus connection failed: {e}")
            time.sleep(self.modbus_config['RETRY_INTERVAL'])
        logging.error(f"Failed to connect to Modbus server after {self.modbus_config['MAX_RETRIES']} attempts.")
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
            :return: One-hot-encoded array (status_one_hot) with status signals if the reading was successfull or None if not
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
                status_one_hot = self.convert_bits(response.registers[0])
                return status_one_hot  # Return processed data if successful
            except Exception as e:
                logging.error(f"Reading the PEMEL status register failed: {e}")
                retries += 1
                time.sleep(self.modbus_config['RETRY_INTERVAL'])
        
        return None  # Return None if all retries failed
    
    def read_pemel_process_values(self):
        """
            Read the Modbus registers for PEMEL process values with retry logic
            :return: Array with process values (pv_values) if the reading was successful or None if not
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
                pv_values = self.convert_process_values(response)
                return pv_values  # Return processed data if successful
            except Exception as e:
                logging.error(f"Reading the PEMEL process values registers failed: {e}")
                retries += 1
                time.sleep(self.modbus_config['RETRY_INTERVAL'])
        
        return None  # Return None if all retries failed
    
    def convert_bits(self, value, bit_length=16):
        """
            Convert a binary number to one-hot encoded array and interpret meanings from YAML config.
            :param value: The value read from the Modbus register.
            :bit_length: The length of the binary number (default is 16).
            :return one_hot: A one-hot encoded array representing the active/inactive state of each bit.
        """
        # # Convert the value to a binary string with leading zeros
        # binary_representation = f"{value:0{bit_length}b}"
        # print(f"Binary representation: {binary_representation}")
        # print("Bit positions:          " + " ".join(f"{i:>2}" for i in range(bit_length - 1, -1, -1)))

        status_config = self.modbus_config.get("PEMEL_STATUS", {})      # Extract the bit interpretation
        one_hot = [0] * bit_length                                      # One-hot encoded array for the bit values

        for i in range(bit_length):
            bit_status = (value >> i) & 1                               # Extract each bit
            one_hot[i] = bit_status                                     # Update the one-hot array

            # Get the bit description from the Modbus config
            bit_description = status_config.get(f"BIT_{i}", "Undefined")
            status = "Active" if bit_status else "Inactive"
            # logging.info(f"Bit {i}: {status} - {bit_description}")
        
        return one_hot
    
    def convert_process_values(self, register):
        """
            Return the process values of the PEMEL.
            :param register: The Modbus register.
            :return pv_values: Process values in an array.
        """
        process_values = self.modbus_config.get("PROCESS_VALUES", {})
        count = process_values.get("COUNT")
        variable_names = [process_values.get(f"REG_{i}", f"Unknown_{i}") for i in range(count)]

        pv_values = []

        # Print and store the results
        # logging.info(("Process Variable Values:")
        for i, value in enumerate(register):
            variable_name = variable_names[i]
            # logging.info((f"{variable_name}: {value}")
            pv_values.append(value)
        
        return pv_values
    
    def write_pemel_current(self, set_h2_flow):
        """
            Converts the hydrogen volume flow rate set point to the PEMEL's electrical current and writes the value to the respective register
            :param set_h2_flow: Hydrogen volume flow rate set point.
        """    
        # Calculate PEMEL current set point according to the desired H2 flow rate
        set_current = self.convert_h2_flow_to_current(set_h2_flow)

        max_retries = self.modbus_config['MAX_RETRIES']
        retries = 0
        while retries < max_retries:
            try:
                # Write the Modbus register for PEMEL current
                write_result = self.client.write_register(self.modbus_config['WRITE_REGISTER'], set_current)

                if write_result.isError():
                    retries += 1
                    raise Exception(f"Error writing value {set_current} to register {self.modbus_config['WRITE_REGISTER']}")
            except Exception as e:
                logging.error(f"Writing the PEMEL current registers failed: {e}")
                retries += 1
                time.sleep(self.modbus_config['RETRY_INTERVAL'])

    def convert_h2_flow_to_current(self, set_h2_flow):
        """
            Convert H2 flow rate to current by reading from a file and interpolating.
            :param set_value: Input H2 flow value
            :return: Converted electrical current value
        """
        try:
            with open(self.modbus_config['H2_FLOW_ARRAY'], "r") as fptr:
                # Skip the header and read the data
                lines = fptr.readlines()
                data = [line.strip().split(';') for line in lines[1:]]  # Read and split data
                
                # Parsing the data into lists
                current_array = [int(row[0]) for row in data]
                h2_flowrate_array = [float(row[1]) for row in data]
                set_current = self.interpolate_h2_flow(current_array, h2_flowrate_array, set_h2_flow)  # Interpolate H2 flow to current
                return set_current
        except Exception as e:
            logging.error(f"Error occurred while converting the hydrogen flow rate into electrical current: {e}")
        return None
          

    def interpolate_h2_flow(self, current_array, h2_flowrate_array, set_h2_flow):
        """
            Interpolate H2 flow rate to determine the current based on the given value.
            :param array: List of H2 flow values
            :param set_value: Input H2 flow value to interpolate
            :return: Interpolated current value
        """
        if set_h2_flow >= max(h2_flowrate_array):               # If the input exceeds the maximum array value
            return self.modbus_config['MAX_CURRENT']
        if set_h2_flow < self.modbus_config['MIN_CURRENT']:     # If the input is below the minimum electrical current
            return 0
        
        for i in range(len(h2_flowrate_array) - 1):
            if h2_flowrate_array[i] <= set_h2_flow <= h2_flowrate_array[i + 1] or h2_flowrate_array[i] >= set_h2_flow >= h2_flowrate_array[i + 1]:
                # Linear interpolation
                slope = (current_array[i + 1] - current_array[i]) / (h2_flowrate_array[i + 1] - h2_flowrate_array[i])
                current_value = current_array[i] + slope * (set_h2_flow - h2_flowrate_array[i])
                return round(current_value)
            else:
                return None
        