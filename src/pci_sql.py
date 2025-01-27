# ----------------------------------------------------------------------------------------------------------------
# PyComInt: Communication interface for chemical plants
# pci_sql.py: 
# > Implements the SQL connection
# ----------------------------------------------------------------------------------------------------------------

import yaml
from datetime import datetime 
import pg8000
import logging

class SQLConnection:
    def __init__(self):
        try:
            # Load SQL configuration
            with open("config/config_sql.yaml", "r") as env_file:
                self.sql_config = yaml.safe_load(env_file)
            self.connection = None
        except Exception as e:
            logging.error(f"Failed to load SQL configuration: {e}")

    def connect(self):
        """
            Establishes a connection to the SQL database.
        """
        try:
            self.connection = pg8000.connect(user=self.sql_config['DB_USER'], 
                                             password=self.sql_config['DB_PASSWORD'],
                                             database=self.sql_config['DB_NAME'], 
                                             host=self.sql_config['DB_HOST'], 
                                             port=self.sql_config['DB_PORT'])
            logging.info(f"Connected to SQL database <{self.sql_config['DB_NAME']}> as {self.sql_config['DB_USER']}")   
            return
        except Exception as e:
            logging.error(f"SQL connection failed: {e}")                                                   
            self.connection = None  # Mark as unavailable

    def is_connected(self):
        """
            Checks if the SQL connection is active.
            :return: True if connected, False otherwise.
        """
        return self.connection is not None
    
    def insert_data(self, values):
        """
            Inserts data into PostgreSQL database using pg8000
            :param values: Process values to store in the SQL database
        """
        try:
            # Get the current timestamp
            current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current date and time
            cursor = self.connection.cursor()

            # Placeholders based on the number of values
            placeholders = ', '.join(['%s'] * (len(values) + 1))  # +1 for the timestamp
            columns = ', '.join(self.sql_config['DB_COLUMNS'])  # Join the column names with commas

            # Check the number of columns and values
            expected_columns_count = len(self.sql_config['DB_COLUMNS'])
            actual_values_count = len(values) + 1  # +1 for the current_timestamp

            assert expected_columns_count == actual_values_count, ValueError(f"Column count mismatch: Expected {expected_columns_count}, got {actual_values_count}. "
                                                                             "Ensure the number of columns matches the values.")

            query = f"INSERT INTO {self.sql_config['DB_TABLE']} ({columns}) VALUES ({placeholders})"

            # Add the timestamp to the values
            values_with_timestamp = [current_timestamp] + values

            # Execute the query
            cursor.execute(query, values_with_timestamp)

            # Commit the transaction
            self.connection.commit()
            
            # Close the cursor
            cursor.close()
        except Exception as e:
            logging.error(f"Error inserting data into PostgreSQL: {e}")
        

    


