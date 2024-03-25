import uuid
import threading

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
