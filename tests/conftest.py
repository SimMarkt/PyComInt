"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

conftest.py: 
> Provides pytest fixtures for mocking configurations and connections for testing
----------------------------------------------------------------------------------------------------
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src import pci_modbus, pci_opcua, pci_sql

@pytest.fixture
def mock_modbus_config(tmp_path: Path) -> dict:
    """ 
    Provide a mock Modbus configuration dictionary.
    :param tmp_path: pytest fixture for temporary directory
    :return: dictionary with mock Modbus configuration
    """
    # Minimal config for Modbus
    return {
        'IP_ADDRESS': '127.0.0.1',
        'PORT': 502,
        'SLAVE_ID': 1,
        'BASE_REGISTER_OFFSET': 0,
        'PEMEL_STATUS': {'ADDRESS': 0x8061},
        'PROCESS_VALUES': {'ADDRESS': 0x8065, 'COUNT': 3},
        'WRITE_REGISTER': 0x8006,
        'MAX_RETRIES': 2,
        'RETRY_INTERVAL': 0,
        'MAX_CURRENT': 52,
        'MIN_CURRENT': 8,
        'H2_FLOW_ARRAY': str(tmp_path / "PEMEL_Current_H2Flowrate.txt"),
    }

@pytest.fixture
def mock_opcua_config() -> dict:
    """
    Provide a mock OPC UA configuration dictionary.
    :return: dictionary with mock OPC UA configuration
    """
    return {
        'URL': 'opc.tcp://localhost:4840',
        'USERNAME': 'user',
        'PASSWORD': 'pass',
        'OPCUA_NODE_IDs': ['ns=7;s=::AsGlobalPV:real_temperature'],
        'H2_FLOW_ID': ['ns=7;s=::AsGlobalPV:real_h2_flowrate'],
    }

@pytest.fixture
def mock_sql_config() -> dict:
    """
    Provide a mock SQL configuration dictionary.
    :return: dictionary with mock SQL configuration
    """
    return {
        'DB_USER': 'user',
        'DB_PASSWORD': 'pass',
        'DB_NAME': 'db',
        'DB_HOST': 'localhost',
        'DB_PORT': 5432,
        'DB_TABLE': 'table',
        'DB_COLUMNS': ['timestamp', 'val1', 'val2'],
    }

@pytest.fixture
def mock_modbus_connection(
        mock_modbus_config: dict
    ) -> pci_modbus.ModbusConnection:
    """
    Provide a mock ModbusConnection object.
    :param monkeypatch: pytest fixture for monkeypatching
    :param mock_modbus_config: fixture providing mock Modbus config
    :return: mocked ModbusConnection instance
    """
    from src import pci_modbus
    conn = pci_modbus.ModbusConnection.__new__(pci_modbus.ModbusConnection)
    conn.modbus_config = mock_modbus_config
    conn.client = MagicMock()
    conn.connected = True
    return conn

@pytest.fixture
def mock_opcua_connection(
        mock_opcua_config: dict
    ) -> pci_opcua.OPCUAConnection:
    """
    Provide a mock OPCUAConnection object.
    :param monkeypatch: pytest fixture for monkeypatching
    :param mock_opcua_config: fixture providing mock OPCUA config
    :return: mocked OPCUAConnection instance
    """
    from src import pci_opcua
    conn = pci_opcua.OPCUAConnection.__new__(pci_opcua.OPCUAConnection)
    conn.opcua_config = mock_opcua_config
    conn.client = MagicMock()
    return conn

@pytest.fixture
def mock_sql_connection(
        mock_sql_config: dict
    ) -> pci_sql.SQLConnection:
    """
    Provide a mock SQLConnection object.
    :param monkeypatch: pytest fixture for monkeypatching
    :param mock_sql_config: fixture providing mock SQL config
    :return: mocked SQLConnection instance
    """
    from src import pci_sql
    conn = pci_sql.SQLConnection.__new__(pci_sql.SQLConnection)
    conn.sql_config = mock_sql_config
    conn.connection = MagicMock()
    return conn
