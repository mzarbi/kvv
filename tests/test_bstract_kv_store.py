import unittest

from store import AbstractKVStore


class TestAbstractKVStore(unittest.TestCase):
    def setUp(self):
        # Setup method to prepare the test environment
        self.store_name = "test_store"
        self.kv_store = AbstractKVStore(backup_dir="test_backups", use_backup=False)

    def test_create_store_success(self):
        result = self.kv_store.create_store(self.store_name)
        self.assertTrue(result)
        self.assertIn(self.store_name, self.kv_store.list_stores())

    def test_create_store_already_exists(self):
        self.kv_store.create_store(self.store_name)
        result = self.kv_store.create_store(self.store_name)
        self.assertFalse(result)

    def test_delete_store_success(self):
        self.kv_store.create_store(self.store_name)
        result = self.kv_store.delete_store(self.store_name)
        self.assertTrue(result)
        self.assertNotIn(self.store_name, self.kv_store.list_stores())

    def test_delete_store_not_exists(self):
        result = self.kv_store.delete_store("nonexistent_store")
        self.assertFalse(result)

    def tearDown(self):
        import shutil
        self.kv_store.shutdown()
        shutil.rmtree("test_backups", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
