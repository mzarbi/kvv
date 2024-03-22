import logging
import time

import Pyro4
import psutil
from threading import Timer

from plugins import StoreDefinitionMixin, TaskDefinitionMixin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

STORE_NAME = "metrics"

@Pyro4.expose
class MetricsPlugin(TaskDefinitionMixin):
    def __init__(self, collect_metrics=False, metrics_interval=60, *args, **kwargs):
        self.collect_metrics = collect_metrics
        self.metrics_interval = metrics_interval
        self.create_store(STORE_NAME)
        if self.collect_metrics:
            super().__init__()

    def _start_mixin_task(self):
        self._metrics_timer = Timer(self.metrics_interval, self._collect_and_schedule_metrics)
        self._metrics_timer.start()

    def _stop_mixin_task(self):
        if hasattr(self, '_metrics_timer'):
            self._metrics_timer.cancel()

    @property
    def _task_name(self):
        return "metrics_collection"

    def add_internal_key(self, key, value, ttl=None, readonly=False):
        """Adds a key to the internal store."""
        kwargs = {'value': value, 'ttl': ttl, 'readonly': readonly, 'last_refresh': time.time()}
        return self._add_key(STORE_NAME, key, **kwargs)

    def delete_internal_key(self, key):
        """Deletes a key from the internal store."""
        return self._delete_key(STORE_NAME, key)

    def edit_internal_key(self, key, value=None, ttl=None, readonly=None):
        """Edits an existing key within the internal store."""
        kwargs = {'value': value, 'ttl': ttl, 'readonly': readonly, 'last_refresh': time.time()}
        return self._edit_key(STORE_NAME, key, **kwargs)

    def get_internal_key(self, key):
        """Retrieves the value of a key from the internal store."""
        return self._get_object(STORE_NAME, key)

    def get_all_internal_keys(self):
        """Retrieves all keys and their values from the internal store."""
        with self._lock:
            store = self._stores.get(STORE_NAME, {})
            # We return a copy to avoid direct modification
            return {key: self._get_object(STORE_NAME, key) for key in store.keys()}

    def _collect_and_schedule_metrics(self):
        # Collect metrics
        self._update_process_metrics()
        # Schedule the next collection if not shutting down
        if not self._shutdown_requested.is_set():
            self._metrics_timer = Timer(self.metrics_interval, self._collect_and_schedule_metrics)
            self._metrics_timer.start()

    def _update_process_metrics(self):
        # Collects metrics and stores them in the internal store
        cpu_usage = psutil.cpu_percent(interval=None)
        memory_usage = psutil.virtual_memory().percent

        # Prepare the tasks' running states to be stored as part of the metrics
        tasks_running_states = {task_name: state for task_name, state in self.is_running.items()}

        # Store the system metrics
        self.add_internal_key("cpu_usage", cpu_usage)
        self.add_internal_key("memory_usage", memory_usage)

        # Store the tasks' running states
        self.add_internal_key("tasks_running_states", tasks_running_states)
