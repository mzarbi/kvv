import logging
from datetime import datetime
import Pyro4

from plugins import StoreDefinitionMixin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

STORE_NAME = "pipelines"
@Pyro4.expose
class WorkflowsPlugin:
    def __init__(self, *args, **kwargs):
        self.create_store(STORE_NAME)

    @property
    def _store_name(self):
        return "pipelines"

    def list_pipelines(self):
        return self._get_all_keys(STORE_NAME)

    def get_pipeline(self, pipeline_id):
        return self._get_all_keys(STORE_NAME).get(pipeline_id, None)

    def add_pipeline(self, pipeline_id, creator, description="", metadata=None, cfg=None, **kwargs):
        pipeline_data = {
            "creator": creator,
            "description": description,
            "metadata": metadata if metadata is not None else {},
            "cfg": cfg if cfg is not None else {},
            "creation_date": datetime.utcnow().isoformat(),
            "last_modified": datetime.utcnow().isoformat(),
            "stages": [],
            "status": "Not Started",
            "errors": []
        }
        self._add_key(STORE_NAME, pipeline_id, **pipeline_data, **kwargs)

    def edit_pipeline(self, pipeline_id, new_description=None, new_metadata=None, new_cfg=None, **kwargs):
        """Edit the description, metadata, or configuration of an existing pipeline with partial updates."""
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            if new_description is not None:
                pipeline_data["description"] = new_description
            if new_metadata is not None:
                pipeline_data["metadata"].update(new_metadata)
            if new_cfg is not None:
                pipeline_data["cfg"].update(new_cfg)  # Partially update cfg
            pipeline_data["last_modified"] = datetime.utcnow().isoformat()
            self._edit_key(STORE_NAME, pipeline_id, **pipeline_data, **kwargs)

    def delete_pipeline(self, pipeline_id):
        self._delete_key(STORE_NAME, pipeline_id)

    def add_stage_to_pipeline(self, pipeline_id, stage_name, depends_on=None, cfg=None, **stage_attrs):
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            new_stage = {
                "name": stage_name,
                "status": "Not Started",
                "depends_on": depends_on or [],
                "cfg": cfg if cfg is not None else {},
                "creation_date": datetime.utcnow().isoformat(),
                "last_modified": datetime.utcnow().isoformat(),
                **stage_attrs
            }
            pipeline_data["stages"].append(new_stage)
            pipeline_data["last_modified"] = datetime.utcnow().isoformat()
            self._edit_key(STORE_NAME, pipeline_id, **pipeline_data)

    def edit_stage_in_pipeline(self, pipeline_id, stage_name, new_status=None, new_cfg=None, new_metadata=None,
                               **new_stage_attrs):
        """Edit an existing stage within a pipeline with partial updates."""
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            for stage in pipeline_data["stages"]:
                if stage["name"] == stage_name:
                    if new_status is not None:
                        stage["status"] = new_status
                    if new_cfg is not None:
                        stage.get("cfg", {}).update(new_cfg)
                    if new_metadata is not None:
                        stage.get("metadata", {}).update(new_metadata)
                    stage.update(new_stage_attrs)
                    stage["last_modified"] = datetime.utcnow().isoformat()
                    break
            pipeline_data["last_modified"] = datetime.utcnow().isoformat()
            self._edit_key(STORE_NAME, pipeline_id, **pipeline_data)

    def delete_stage_from_pipeline(self, pipeline_id, stage_name):
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            pipeline_data["stages"] = [stage for stage in pipeline_data["stages"] if stage["name"] != stage_name]
            pipeline_data["last_modified"] = datetime.utcnow().isoformat()
            self._edit_key(STORE_NAME, pipeline_id, **pipeline_data)

    def log_pipeline_error(self, pipeline_id, error_message):
        """Logs an error message to the specified pipeline."""
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            if "errors" not in pipeline_data:
                pipeline_data["errors"] = []
            pipeline_data["errors"].append({"message": error_message, "timestamp": datetime.utcnow().isoformat()})
            self._edit_key(STORE_NAME, pipeline_id, **pipeline_data)
        else:
            logger.error(f"Pipeline {pipeline_id} does not exist for error logging.")

    def log_stage_error(self, pipeline_id, stage_name, error_message):
        """Logs an error message to a specific stage within a pipeline."""
        pipeline_data = self._get_object(STORE_NAME, pipeline_id)
        if pipeline_data:
            stage_found = False
            for stage in pipeline_data["stages"]:
                if stage["name"] == stage_name:
                    if "errors" not in stage:
                        stage["errors"] = []
                    stage["errors"].append({"message": error_message, "timestamp": datetime.utcnow().isoformat()})
                    stage_found = True
                    break
            if stage_found:
                self._edit_key(STORE_NAME, pipeline_id, **pipeline_data)
            else:
                logger.error(f"Stage {stage_name} not found in pipeline {pipeline_id} for error logging.")
        else:
            logger.error(f"Pipeline {pipeline_id} does not exist for error logging.")