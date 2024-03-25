import threading
import uuid
from core.service import synchronized


class Stage:
    def __init__(self, name, status='pending'):
        self.id = str(uuid.uuid4())
        self.name = name
        self.status = status

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'status': self.status}

class Pipeline:
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.name = name
        self.stages = []

    def add_stage(self, stage):
        self.stages.append(stage)

    def to_dict(self):
        return {'id': self.id, 'name': self.name, 'stages': [stage.to_dict() for stage in self.stages]}

class PipelineManager:
    def __init__(self):
        self.pipelines = {}
        self.lock = threading.Lock()

    @synchronized
    def create_pipeline(self, name):
        """
        Creates a new pipeline with the given name and returns its ID.
        """
        with self.lock:
            new_pipeline = Pipeline(name)
            self.pipelines[new_pipeline.id] = new_pipeline
            return new_pipeline.id

    @synchronized
    def add_stage_to_pipeline(self, pipeline_id, stage_name):
        """
        Adds a new stage to the specified pipeline.
        """
        with self.lock:
            if pipeline_id in self.pipelines:
                new_stage = Stage(stage_name)
                self.pipelines[pipeline_id].add_stage(new_stage)
                return new_stage.id
            else:
                raise ValueError("Pipeline not found")

    @synchronized
    def get_pipeline(self, pipeline_id):
        """
        Retrieves a pipeline by its ID.
        """
        with self.lock:
            if pipeline_id in self.pipelines:
                return self.pipelines[pipeline_id].to_dict()
            else:
                raise ValueError("Pipeline not found")

    @synchronized
    def list_pipelines(self):
        """
        Lists all pipelines.
        """
        with self.lock:
            return [pipeline.to_dict() for pipeline in self.pipelines.values()]

    def shutdown(self):
        """
        Placeholder for any required shutdown procedures.
        """
        pass  # No specific shutdown actions needed for this simple implementation
