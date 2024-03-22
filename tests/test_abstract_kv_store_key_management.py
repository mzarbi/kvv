import json
import os
import time
import unittest

from store import AbstractKVStore


class TestAbstractKVStoreKeyManagement(unittest.TestCase):
    def setUp(self):
        # Setup method to prepare the test environment
        self.store_name = "test_store"
        self.key = "test_key"
        self.value = "test_value"
        self.kv_store = AbstractKVStore(backup_dir="test_backups", use_backup=False, cleanup_frequency=10, max_backups=2)
        self.kv_store.create_store(self.store_name)

    def test_add_key_to_store(self):
        result = self.kv_store._add_key(self.store_name, self.key, value=self.value)
        self.assertTrue(result)
        retrieved_value = self.kv_store._get_key(self.store_name, self.key)
        self.assertEqual(retrieved_value, self.value)

    def test_add_key_to_nonexistent_store(self):
        result = self.kv_store._add_key("nonexistent_store", self.key, value=self.value)
        self.assertFalse(result)

    def test_delete_key_from_store(self):
        self.kv_store._add_key(self.store_name, self.key, value=self.value)
        result = self.kv_store._delete_key(self.store_name, self.key)
        self.assertTrue(result)
        self.assertNotIn(self.key, self.kv_store._stores[self.store_name])

    def test_delete_nonexistent_key(self):
        result = self.kv_store._delete_key(self.store_name, "nonexistent_key")
        self.assertFalse(result)

    def test_edit_key_in_store(self):
        new_value = "new_test_value"
        self.kv_store._add_key(self.store_name, self.key, value=self.value)
        result = self.kv_store._edit_key(self.store_name, self.key, value=new_value)
        self.assertTrue(result)
        updated_value = self.kv_store._get_key(self.store_name, self.key)
        self.assertEqual(updated_value, new_value)

    def test_edit_nonexistent_key(self):
        result = self.kv_store._edit_key(self.store_name, "nonexistent_key", value="new_value")
        self.assertFalse(result)

    # Testing expiration and cleanup
    def test_key_expiration(self):
        self.kv_store._add_key(self.store_name, self.key, value=self.value, ttl=1)  # 1 second TTL
        time.sleep(2)  # Wait for the key to expire
        self.assertIsNone(self.kv_store._get_key(self.store_name, self.key))

    # Testing backup functionality
    def test_rotate_and_backup(self):
        self.kv_store._add_key(self.store_name, self.key, value=self.value)
        self.kv_store.rotate_and_backup(self.store_name, self.kv_store._stores[self.store_name])
        backup_path = os.path.join(self.kv_store.backup_dir, f"{self.store_name}.backup.1.json")
        self.assertTrue(os.path.exists(backup_path))
        with open(backup_path, 'r') as backup_file:
            backup_content = json.load(backup_file)
            self.assertEqual(backup_content[self.key]['value'], self.value)

    def tearDown(self):
        # Clean up any resources used in tests
        import shutil
        self.kv_store.shutdown()
        shutil.rmtree("test_backups", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
