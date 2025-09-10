"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_threads.py: 
> Tests the threading functions for PEMEL control and data storage
----------------------------------------------------------------------------------------------------
"""

from unittest.mock import MagicMock, patch

def test_el_control_func(mock_modbus_connection, mock_opcua_connection):
    # status_one_hot[10] == 1 triggers write
    mock_modbus_connection.read_pemel_status.return_value = [0]*10 + [1] + [0]*5
    mock_opcua_connection.read_node_values.return_value = {'id': 5.0}
    mock_modbus_connection.write_pemel_current = MagicMock()
    from src.pci_threads import el_control_func
    last_log_time = 0
    result = el_control_func(mock_modbus_connection, mock_opcua_connection, last_log_time)
    assert isinstance(result, float)

def test_data_trans_func(mock_modbus_connection, mock_opcua_connection, mock_sql_connection):
    mock_modbus_connection.read_pemel_status.return_value = [1]*16
    mock_modbus_connection.read_pemel_process_values.return_value = [1,2,3]
    mock_opcua_connection.read_node_values.return_value = {'id': 1.0, 'id2': 2.0}
    mock_sql_connection.insert_data = MagicMock()
    from src.pci_threads import data_trans_func
    data_trans_func(mock_modbus_connection, mock_opcua_connection, mock_sql_connection)
    assert mock_sql_connection.insert_data.called