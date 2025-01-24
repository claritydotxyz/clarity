import pytest
import os
from clarity.data.storage.encrypted import EncryptedStorage
from clarity.data.storage.local import LocalStorage

async def test_encrypted_storage():
    storage = EncryptedStorage()
    test_data = {"key": "value"}
    test_path = "test_encrypted.dat"
    
    await storage.save(test_data, test_path)
    loaded_data = await storage.load(test_path)
    
    assert loaded_data == test_data
    os.remove(test_path)

async def test_local_storage():
    storage = LocalStorage("./test_storage")
    test_data = {"key": "value"}
    test_file = "test.json"
    
    await storage.save(test_data, test_file)
    loaded_data = await storage.load(test_file)
    
    assert loaded_data == test_data
    os.remove(f"./test_storage/{test_file}")
