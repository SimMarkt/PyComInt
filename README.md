# PyComInt

## Overview

**PyComInt** is a communication interface designed for chemical plants. It facilitates multi-threaded data transfer between an **OPC UA server**, a **Modbus client**, and an **SQL database**. 

### Application

PyComInt has been applied to a **Power-to-Gas** process, integrating:
- A **proton exchange membrane electrolyzer (PEMEL)** as a Modbus client.
- A **biological methanation unit (BM)** with a programmable logic controller (PLC) providing an OPC UA server.

This tool supports efficient data management and process control in industrial applications by ensuring reliable communication between different system components.

---

## Project Structure

The project is organized into the following directories and files:

```plaintext
PyComInt/
│
├── config/
│   ├── config_gen.yaml
│   ├── config_modbus.yaml
│   ├── config_opcua.yaml
│   └── config_sql.yaml
│
├── src/
│   ├── pci_modbus.py
│   ├── pci_opcua.py
│   ├── pci_sql.py
│   └── threads.py
│
├── pci_main.py
├── pci_main_ws.py
└── requirements.txt

```

### `config/`
Contains configuration files for various components of the project:
- **`config/config_gen.yaml`**: General configuration for main connection tasks and logging.
- **`config/config_modbus.yaml`**: Configuration for the Modbus client, including details for decrypting bit-wise signals.
- **`config/config_opcua.yaml`**: Configuration for the OPC UA server and tagged nodes.
- **`config/config_sql.yaml`**: Configuration for the SQL database (PostgreSQL).

### `src/`
Contains source code for the different threads and connection wrappers:
- **`src/pci_modbus.py`**: Implements the Modbus connection with a class object providing:
  - `connect()`, `is_connected()`, `read_pemel_status()`, `read_pemel_process_values()`, `write_pemel_current()`.
- **`src/pci_opcua.py`**: Implements the OPC UA connection with a class object providing:
  - `connect()`, `is_connected()`, `read_node_values()`.
- **`src/pci_sql.py`**: Implements the SQL connection with a class object providing:
  - `connect()`, `is_connected()`, `insert_data()`.
- **`src/threads.py`**: Implements multi-threaded operations, including:
  - **PEMEL control thread**: Manages PEMEL operations using Modbus and OPC UA.
  - **Data storage thread**: Handles data transfer between the OPC UA server, Modbus client, and SQL database.
  - **Supervisor thread**: Monitors and attempts reconnection for disconnected services.

### Main Scripts
- **`pci_main.py`**: The primary script for running multi-threaded data transfer operations.
- **`pci_main_ws.py`**: A variation of the main script designed to set up a Windows service for data transfer.

---

## Usage

1. Configure the project using the YAML files located in the `config/` directory.
2. Run `pci_main.py` for a standard multi-threaded data transfer operation.
3. Optionally, set up `pci_main_ws.py` as a Windows service for seamless background execution.
4. The code furthermore creates a log file `PyComInt.log` for debugging and monitoring. 

---

## Requirements

- Python 3.8+
- Required libraries:
  - `pymodbus`
  - `opcua`
  - `PyYAML`
  - `pywin32`
  - `cryptography`
  - `pg8000`

---

## Contributing

Contributions are welcome! Feel free to submit issues on [GitHub](https://github.com/SimMarkt/PyComInt).

---

## License

This project is licensed under the [MIT License](LICENSE).
