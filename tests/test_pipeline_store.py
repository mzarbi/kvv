import unittest

from plugins.workflows import WorkflowsPlugin
from store import AbstractKVStore


class EnhancedKVStore(AbstractKVStore, WorkflowsPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        WorkflowsPlugin.__init__(self, *args, **kwargs)


class TestPipelineManagementMixin(unittest.TestCase):
    def setUp(self):
        self.kv_store = EnhancedKVStore(backup_dir="test_backups", use_backup=False)
        self.kv_store.start_tasks()

    def tearDown(self):
        self.kv_store.shutdown()

    def test_add_and_get_pipeline(self):
        self.kv_store.add_pipeline("pipeline1", "creator1", "Sample pipeline")
        pipeline_info = self.kv_store._get_object("pipelines", "pipeline1")
        self.assertEqual(pipeline_info['creator'], "creator1")
        self.assertEqual(pipeline_info['description'], "Sample pipeline")

    def test_edit_pipeline_partial_cfg(self):
        initial_cfg = {"setting1": "value1"}
        self.kv_store.add_pipeline("pipeline1", "creator1", cfg=initial_cfg)
        self.kv_store.edit_pipeline("pipeline1", new_cfg={"setting2": "value2"})

        pipeline_info = self.kv_store._get_object("pipelines", "pipeline1")
        self.assertIn("setting1", pipeline_info['cfg'])
        self.assertIn("setting2", pipeline_info['cfg'])
        self.assertEqual(pipeline_info['cfg']['setting2'], "value2")

    def test_add_and_edit_stage_in_pipeline(self):
        self.kv_store.add_pipeline("pipeline1", "creator1")
        self.kv_store.add_stage_to_pipeline("pipeline1", "stage1", cfg={"stage_setting": "initial"})
        self.kv_store.edit_stage_in_pipeline("pipeline1", "stage1", new_cfg={"stage_setting": "updated"})

        pipeline_info = self.kv_store._get_object("pipelines", "pipeline1")
        stage_info = next((stage for stage in pipeline_info['stages'] if stage['name'] == "stage1"), None)
        self.assertIsNotNone(stage_info)
        self.assertEqual(stage_info['cfg']['stage_setting'], "updated")

    def test_delete_pipeline_and_stage(self):
        self.kv_store.add_pipeline("pipeline1", "creator1")
        self.kv_store.add_stage_to_pipeline("pipeline1", "stage1")
        self.kv_store.delete_stage_from_pipeline("pipeline1", "stage1")
        self.kv_store.delete_pipeline("pipeline1")

        self.assertIsNone(self.kv_store._get_object("pipelines", "pipeline1"))


if __name__ == "__main__":
    unittest.main()
