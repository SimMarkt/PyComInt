"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_sql.py: 
> Tests the SQL connection and insertion of data
----------------------------------------------------------------------------------------------------
"""

from unittest.mock import MagicMock

def test_insert_data(mock_sql_connection: "pci_sql.SQLConnection") -> None:
    """
    Test inserting data into SQL database.
    :param mock_sql_connection: Fixture providing a SQLConnection instance
    """
    mock_cursor = MagicMock()
    mock_sql_connection.connection.cursor.return_value = mock_cursor
    mock_sql_connection.sql_config['DB_COLUMNS'] = ['timestamp', 'val1', 'val2']
    mock_sql_connection.insert_data([1, 2])
    assert mock_cursor.execute.called
    assert mock_sql_connection.connection.commit.called
    assert mock_cursor.close.called
