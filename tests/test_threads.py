"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_threads.py: 
> Tests the threading functions for PEMEL control and data storage
----------------------------------------------------------------------------------------------------
"""

from unittest.mock import MagicMock

def test_el_control_func(
        mock_modbus_connection: "pci_modbus.ModbusConnection",
        mock_opcua_connection: "pci_opcua.OPCUAConnection"
    ) -> None:
    """
    Test the PEMEL control function.
    :param mock_modbus_connection: Fixture providing a ModbusConnection instance
    :param mock_opcua_connection: Fixture providing an OPCUAConnection instance
    """
    mock_modbus_connection.read_pemel_status = MagicMock(return_value=[0]*10 + [1] + [0]*5)
    mock_opcua_connection.read_node_values = MagicMock(return_value={'id': 5.0})
    mock_modbus_connection.write_pemel_current = MagicMock()

    from src.pci_threads import el_control_func
    last_log_time = 0
    result = el_control_func(mock_modbus_connection, mock_opcua_connection, last_log_time)
    assert isinstance(result, float)

def test_data_trans_func(
        mock_modbus_connection: "pci_modbus.ModbusConnection",
        mock_opcua_connection: "pci_opcua.OPCUAConnection",
        mock_sql_connection: "pci_sql.SQLConnection"
    ) -> None:
    """
    Test the data transmission function.
    :param mock_modbus_connection: Fixture providing a ModbusConnection instance
    :param mock_opcua_connection: Fixture providing an OPCUAConnection instance
    :param mock_sql_connection: Fixture providing a SQLConnection instance
    """
    mock_modbus_connection.read_pemel_status = MagicMock(return_value=[1]*16)
    mock_modbus_connection.read_pemel_process_values = MagicMock(return_value=[1, 2, 3])
    mock_opcua_connection.read_node_values = MagicMock(return_value={'id': 1.0, 'id2': 2.0})
    mock_sql_connection.insert_data = MagicMock()

    from src.pci_threads import data_trans_func
    data_trans_func(mock_modbus_connection, mock_opcua_connection, mock_sql_connection)
    assert mock_sql_connection.insert_data.called
