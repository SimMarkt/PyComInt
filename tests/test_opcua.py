"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_opcua.py: 
> Tests the OPCUA connection and reading of node values
----------------------------------------------------------------------------------------------------
"""

from unittest.mock import MagicMock

def test_read_node_values(mock_opcua_connection):
    # Patch client.get_node().get_value()
    node_mock = MagicMock()
    node_mock.get_value.return_value = 42
    mock_opcua_connection.client.get_node.return_value = node_mock

    result = mock_opcua_connection.read_node_values('AllNodes')
    assert isinstance(result, dict)
    for v in result.values():
        assert v == 42
