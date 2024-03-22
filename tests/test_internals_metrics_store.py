import time
import unittest

from plugins.metrics import MetricsPlugin
from store import AbstractKVStore


class EnhancedKVStore(AbstractKVStore, MetricsPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        MetricsPlugin.__init__(self, *args, **kwargs)


class TestInternalKVStoreMixin(unittest.TestCase):
    def setUp(self):
        # Initialize the store without starting metrics collection
        self.kv_store = EnhancedKVStore(collect_metrics=True, backup_dir="test_backups", use_backup=False,
                                        metrics_interval=1)
        self.kv_store.start_tasks()

    def tearDown(self):
        import shutil
        self.kv_store.shutdown()
        shutil.rmtree("test_backups", ignore_errors=True)

    def test_periodic_metrics_update(self):
        # Allow some time for the metrics update task to run
        time.sleep(5)  # Sleep slightly longer than the metrics interval

        cpu_usage = self.kv_store.get_internal_key("cpu_usage")
        memory_usage = self.kv_store.get_internal_key("memory_usage")

        # Verify that some metrics were collected
        self.assertIsNotNone(cpu_usage)
        self.assertIsNotNone(memory_usage)


if __name__ == "__main__":
    unittest.main()
