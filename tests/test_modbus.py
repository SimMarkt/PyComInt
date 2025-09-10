"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_modbus.py: 
> Tests the Modbus connection and its methods
----------------------------------------------------------------------------------------------------
"""
import os

import pytest
from unittest.mock import MagicMock, patch

def test_read_pemel_status(mock_modbus_connection: "pci_modbus.ModbusConnection") -> None:
    # Mock the client response
    mock_response = MagicMock()
    mock_response.isError.return_value = False
    mock_response.registers = [0b1010101010101010]
    mock_modbus_connection.client.read_holding_registers.return_value = mock_response

    result = mock_modbus_connection.read_pemel_status()
    assert isinstance(result, list)
    assert len(result) == 16

def test_read_pemel_process_values(mock_modbus_connection: "pci_modbus.ModbusConnection") -> None:
    mock_response = MagicMock()
    mock_response.isError.return_value = False
    mock_response.registers = [1, 2, 3]
    mock_modbus_connection.client.read_holding_registers.return_value = mock_response

    result = mock_modbus_connection.read_pemel_process_values()
    assert result == [1, 2, 3]

def test_write_pemel_current(mock_modbus_connection, monkeypatch):
    """
    Test writing current to PEMEL via Modbus.
    :param mock_modbus_connection: Fixture providing a ModbusConnection instance
    :param monkeypatch: Pytest fixture for patching
    """
    mock_modbus_connection.convert_h2_flow_to_current = MagicMock(return_value=42)
    mock_modbus_connection.client.write_register.return_value.isError.return_value = False
    mock_modbus_connection.write_pemel_current(10.0)
    mock_modbus_connection.client.write_register.assert_called()

def test_convert_bits(mock_modbus_connection):
    result = mock_modbus_connection.convert_bits(0b1010, bit_length=4)
    assert result == [0, 1, 0, 1]

def test_convert_h2_flow_to_current(mock_modbus_connection):
    """
    Test the conversion of H2 flowrate to current using interpolation.
    :param mock_modbus_connection: Fixture providing a ModbusConnection instance
    """
    mock_modbus_connection.modbus_config['H2_FLOW_ARRAY'] = os.path.join(
        os.path.dirname(__file__), "..", "PEMEL_Current_H2Flowrate.txt"
    )
    # Use the path already set in mock_modbus_connection.modbus_config['H2_FLOW_ARRAY']
    result = mock_modbus_connection.convert_h2_flow_to_current(7.5)
    result1 = mock_modbus_connection.convert_h2_flow_to_current(16.7)
    result2 = mock_modbus_connection.convert_h2_flow_to_current(2)
    result3 = mock_modbus_connection.convert_h2_flow_to_current(23.7)
    assert isinstance(result, int)
    assert result == 21
    assert result1 == 47
    assert result2 == 0, "Minimum h2 flowrate should return 0 current!"
    assert result3 == 52, "Maximum h2 flowrate should return 52 current!"  

def test_interpolate_h2_flow(mock_modbus_connection):
    """
    Test the interpolation function for H2 flowrate to current conversion.
    :param mock_modbus_connection: Fixture providing a ModbusConnection instance
    """
    current_array = [10, 20, 30]
    h2_flowrate_array = [5.0, 10.0, 15.0]
    # Between 5.0 and 10.0
    result = mock_modbus_connection.interpolate_h2_flow(current_array, h2_flowrate_array, 7.5)
    assert isinstance(result, int)
    # Above max
    result = mock_modbus_connection.interpolate_h2_flow(current_array, h2_flowrate_array, 20.0)
    assert result == mock_modbus_connection.modbus_config['MAX_CURRENT']
    # Below min
    result = mock_modbus_connection.interpolate_h2_flow(current_array, h2_flowrate_array, 1.0)
    assert result == 0
