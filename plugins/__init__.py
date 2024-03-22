import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

class StoreDefinitionMixin:
    @property
    def _store_name(self):
        raise NotImplementedError


class TaskDefinitionMixin:
    def __init__(self):
        self.register_task(self._task_name, self._start_mixin_task,
                           self._stop_mixin_task)

    def _start_mixin_task(self):
        raise NotImplementedError

    def _stop_mixin_task(self):
        raise NotImplementedError

    @property
    def _task_name(self):
        raise NotImplementedError

