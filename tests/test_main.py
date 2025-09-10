"""
----------------------------------------------------------------------------------------------------
PyComInt: Communication interface for chemical plants
https://github.com/SimMarkt/PyComInt

test_main.py: 
> Tests the main module, focusing on multithreading and integration of components
----------------------------------------------------------------------------------------------------
"""

import threading
import time
import pytest
from unittest.mock import patch, MagicMock

def test_multithreading_runs(monkeypatch):
    # Patch connections and threads to avoid real side effects
    with patch("src.pci_modbus.ModbusConnection") as MockModbus, \
         patch("src.pci_opcua.OPCUAConnection") as MockOPCUA, \
         patch("src.pci_sql.SQLConnection") as MockSQL, \
         patch("src.pci_threads.pemel_control", return_value=None), \
         patch("src.pci_threads.data_storage", return_value=None), \
         patch("src.pci_threads.supervisor", return_value=None), \
         patch("builtins.open", create=True), \
         patch("yaml.safe_load", return_value={
             'PEMEL_CONTROL_INTERVAL': 0.01,
             'DATA_STORAGE_INTERVAL': 0.01,
             'RECONNECTION_INTERVAL': 0.01,
         }), \
         patch("logging.basicConfig"), \
         patch("logging.getLogger"), \
         patch("logging.info"), \
         patch("logging.error"):
        import pci_main
        # Patch time.sleep to break the infinite loop after a short time
        with patch("time.sleep", side_effect=[None, None, Exception("break")]):
            try:
                pci_main.main()
            except Exception as e:
                assert str(e) == "break"