import time
import unittest
from unittest.mock import patch, Mock

from plugins.metrics import MetricsPlugin
from store import AbstractKVStore


class EnhancedKVStore(AbstractKVStore, MetricsPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MetricsPlugin.__init__(self, *args, **kwargs)


class TestInternalKVStoreMixin(unittest.TestCase):
    def setUp(self):
        # Initialize the store without starting metrics collection
        self.kv_store = EnhancedKVStore(collect_metrics=False, backup_dir="test_backups", use_backup=False)
        self.kv_store.start_tasks()

    def tearDown(self):
        import shutil
        self.kv_store.shutdown()
        shutil.rmtree("test_backups", ignore_errors=True)

    def test_add_and_get_internal_key(self):
        self.kv_store.add_internal_key("test_key", "test_value")
        result = self.kv_store.get_internal_key("test_key")['value']
        self.assertEqual(result, "test_value")

    def test_edit_internal_key(self):
        self.kv_store.add_internal_key("test_key", "initial_value")
        self.kv_store.edit_internal_key("test_key", "updated_value")
        result = self.kv_store.get_internal_key("test_key")['value']
        self.assertEqual(result, "updated_value")

    def test_delete_internal_key(self):
        self.kv_store.add_internal_key("test_key", "test_value")
        self.kv_store.delete_internal_key("test_key")
        result = self.kv_store.get_internal_key("test_key")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
