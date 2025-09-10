import pytest
from unittest.mock import MagicMock, patch
from src.pci_modbus import ModbusConnection
from src.pci_opcua import OPCUAConnection
from src.pci_sql import SQLConnection

# Python


# Absolute imports for the namespace package

@pytest.fixture
def modbus_connection():
    with patch("src.pci_modbus.ModbusConnection.connect", return_value=None):
        conn = ModbusConnection()
        conn.modbus_config = {
            'MAX_RETRIES': 1,
            'MAX_CURRENT': 52,
            'MIN_CURRENT': 8,
            'H2_FLOW_ARRAY': 'dummy.txt'
        }
        conn.client = MagicMock()
        conn.connected = True
        yield conn

@pytest.fixture
def opcua_connection():
    with patch("src.pci_opcua.OPCUAConnection.connect", return_value=None):
        conn = OPCUAConnection()
        conn.opcua_config = {
            'OPCUA_NODE_IDs': ["ns=7;s=::AsGlobalPV:real_temperature"],
            'H2_FLOW_ID': ["ns=7;s=::AsGlobalPV:real_h2_flowrate"]
        }
        conn.client = MagicMock()
        yield conn

@pytest.fixture
def sql_connection():
    with patch("src.pci_sql.SQLConnection.connect", return_value=None):
        conn = SQLConnection()
        conn.sql_config = {
            'DB_USER': 'user',
            'DB_PASSWORD': 'pass',
            'DB_NAME': 'db',
            'DB_HOST': 'localhost',
            'DB_PORT': 5432,
            'DB_TABLE': 'table',
            'DB_COLUMNS': ['timestamp', 'col1', 'col2']
        }
        conn.connection = MagicMock()
        yield conn

@pytest.fixture(autouse=True)
def patch_sleep():
    with patch("time.sleep", return_value=None):
        yield