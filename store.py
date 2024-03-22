import json
import os
import time
import logging
import threading

import Pyro4
from cryptography.fernet import Fernet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

@Pyro4.expose
class AbstractKVStore:
    def __init__(self, status_ttl=3600 * 10, cleanup_frequency=60, backup_dir=None, max_backups=10, use_backup=False, *args, **kwargs):
        self.status_ttl = status_ttl
        self.cleanup_frequency = cleanup_frequency
        self.max_backups = max_backups
        self.backup_dir = backup_dir
        self._stores = {}

        try:
            os.makedirs(self.backup_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"Failed to create/access backup directory {self.backup_dir}: {e}")

        if use_backup:
            self.load_from_backup()

        self._lock = threading.RLock()
        self._shutdown_requested = threading.Event()

        self._tasks = {}
        self._shutdown_tasks = {}
        self.is_running = {}
        # Register and start tasks
        self.register_task("cleanup", self._start_cleanup_thread, self._stop_cleanup_thread)

    def start_task_by_name(self, task_name):
        if task_name in self._tasks and not self.is_running.get(task_name, False):
            logger.info(f"Starting task: {task_name}")
            self._tasks[task_name]()  # Start the task
            self.is_running[task_name] = True
            logger.info(f"Task {task_name} has been started.")
        elif self.is_running.get(task_name, False):
            logger.info(f"Task {task_name} is already running.")
        else:
            logger.error(f"No task named {task_name} found.")

    def shutdown_task_by_name(self, task_name):
        if task_name in self._shutdown_tasks and self.is_running.get(task_name, False):
            logger.info(f"Shutting down task: {task_name}")
            self._shutdown_tasks[task_name]()  # Shutdown the task
            self.is_running[task_name] = False
            logger.info(f"Task {task_name} has been shut down.")
        elif not self.is_running.get(task_name, False):
            logger.info(f"Task {task_name} is not running or does not exist.")
        else:
            logger.error(f"No task named {task_name} found.")

    def start_tasks(self, task_name=None):
        if task_name:
            # Start a specific task by its name
            self.start_task_by_name(task_name)
        else:
            # Start all tasks if no task name is provided
            for name in self._tasks.keys():
                self.start_task_by_name(name)

    def shutdown(self, task_name=None):
        if task_name:
            # Shutdown a specific task by its name
            self.shutdown_task_by_name(task_name)
        else:
            # Shutdown all tasks if no task name is provided
            for name in self._shutdown_tasks.keys():
                self.shutdown_task_by_name(name)

    def update_configuration(self, backup_dir=None, metrics_interval=None, status_ttl=None, cleanup_frequency=None):
        if backup_dir is not None:
            self.backup_dir = backup_dir
            os.makedirs(self.backup_dir, exist_ok=True)

        if metrics_interval is not None:
            self.metrics_interval = metrics_interval

        if status_ttl is not None:
            self.status_ttl = status_ttl

        if cleanup_frequency is not None:
            self.cleanup_frequency = cleanup_frequency

        logger.info("Configuration updated.")

    def get_configuration(self):
        """Returns the current configuration settings."""
        return {
            "status_ttl": self.status_ttl,
            "cleanup_frequency": self.cleanup_frequency,
            "max_backups": self.max_backups,
            "backup_dir": self.backup_dir,
            "metrics_interval": getattr(self, 'metrics_interval', None)
        }

    def register_task(self, name, start_task, stop_task):
        self._tasks[name] = start_task
        self._shutdown_tasks[name] = stop_task
        self.is_running[name] = False

    def _stop_cleanup_thread(self):
        self._shutdown_requested.set()
        if hasattr(self, '_cleanup_thread') and self._cleanup_thread is not None:
            self._cleanup_thread.join()
            logger.info("Cleanup thread has been shut down gracefully.")

    def _start_cleanup_thread(self):
        self._cleanup_thread = threading.Thread(target=self.cleanup)
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()

    def cleanup(self):
        while not self._shutdown_requested.is_set():
            with self._lock:
                for k, v in self._stores.items():
                    current_time = time.time()
                    expired_keys = [key for key, value_details in v.items() if
                                    current_time > value_details['exp_time']]
                    for key in expired_keys:
                        del v[key]
                        logger.info(f"Expired value for key {key} removed")
                    self.rotate_and_backup(k, v)
            self._shutdown_requested.wait(self.cleanup_frequency)

    def load_from_backup(self):
        raise NotImplementedError("load_from_backup method not implemented")

    def rotate_and_backup(self, store_name, store_content):
        if not isinstance(store_name, str) or not store_name:
            raise ValueError("store_name must be a non-empty string")
        for i in range(self.max_backups, 0, -1):
            src = os.path.join(self.backup_dir, f"{store_name}.backup.{i}.json")
            dst = os.path.join(self.backup_dir, f"{store_name}.backup.{i + 1}.json")
            if os.path.exists(src):
                if i == self.max_backups:
                    os.remove(src)
                else:
                    os.rename(src, dst)
        current_backup = os.path.join(self.backup_dir, f"{store_name}.backup.1.json")
        with open(current_backup, 'w') as f:
            json.dump(store_content, f, ensure_ascii=False, indent=4)

    def create_store(self, store_name):
        if not isinstance(store_name, str) or not store_name:
            raise ValueError("store_name must be a non-empty string")

        with self._lock:
            if store_name in self._stores:
                logger.info(f"Store {store_name} already exists.")
                return False
            else:
                self._stores[store_name] = {}
                logger.info(f"Store {store_name} created successfully.")
                return True

    def delete_store(self, store_name):
        if not isinstance(store_name, str) or not store_name:
            raise ValueError("store_name must be a non-empty string")

        with self._lock:
            if store_name in self._stores:
                del self._stores[store_name]
                logger.info(f"Store {store_name} deleted successfully.")
                return True
            else:
                logger.info(f"Store {store_name} does not exist.")
                return False

    def list_stores(self):
        return list(self._stores.keys())

    def _get_all_keys(self, store_name):
        return self._stores.get(store_name, None)

    def display(self):
        print(json.dumps(self._stores, indent=5))

    def _add_key(self, store_name, key, **kwargs):
        with self._lock:
            store = self._stores.get(store_name)
            if store is None:
                logger.error(f"Store {store_name} does not exist.")
                return False

            if key in store and store[key].get('readonly', False):
                logger.error(f"Attempt to modify readonly key: {key}")
                return False

            if kwargs.get('ttl') is None:
                kwargs['ttl'] = 10 * 365 * 24 * 60 * 60  # 10 years in seconds
            kwargs['exp_time'] = time.time() + kwargs['ttl']
            del kwargs['ttl']

            store[key] = kwargs
            logger.info(f"Key {key} added to store {store_name} successfully.")
            return True

    def _delete_key(self, store_name, key):
        with self._lock:
            store = self._stores.get(store_name)
            if store is None or key not in store:
                logger.error(f"Key {key} or store {store_name} does not exist.")
                return False

            del store[key]
            logger.info(f"Key {key} deleted from store {store_name} successfully.")
            return True

    def _edit_key(self, store_name, key, **kwargs):
        with self._lock:
            store = self._stores.get(store_name)
            if store is None:
                logger.error(f"Store {store_name} does not exist.")
                return False
            if key not in store:
                logger.error(f"key {key} does not exist.")
                store = self._stores.get(store_name)
                if store is None:
                    logger.error(f"Store {store_name} does not exist.")
                    return False

                if key in store and store[key].get('readonly', False):
                    logger.error(f"Attempt to modify readonly key: {key}")
                    return False

                if kwargs.get('ttl') is None:
                    kwargs['ttl'] = 10 * 365 * 24 * 60 * 60  # 10 years in seconds
                kwargs['exp_time'] = time.time() + kwargs['ttl']
                del kwargs['ttl']

                store[key] = kwargs
                logger.info(f"Key {key} added to store {store_name} successfully.")
                return True

            if 'ttl' in kwargs:
                if kwargs.get('ttl') is None:
                    kwargs['ttl'] = 10 * 365 * 24 * 60 * 60  # 10 years in seconds
                kwargs['exp_time'] = time.time() + kwargs['ttl']
                del kwargs['ttl']  # Convert 'ttl' to 'exp_time'

            if store[key].get('readonly', False) and not kwargs.get('force', False):
                logger.error(f"Attempt to modify readonly key: {key}")
                return False

            store[key].update(kwargs)
            logger.info(f"Key {key} in store {store_name} updated successfully.")
            return True

    def _get_key(self, store_name, key):
        with self._lock:
            store = self._stores.get(store_name)
            if store is None:
                logger.error(f"Store {store_name} does not exist.")
                return None

            key_data = store.get(key)
            if key_data is None:
                logger.info(f"Key {key} does not exist in store {store_name}.")
                return None

            # Check if the key has expired
            current_time = time.time()
            if 'exp_time' in key_data and current_time > key_data['exp_time']:
                logger.info(f"Key {key} in store {store_name} has expired.")
                return None

            return key_data.get('value')

    def _get_object(self, store_name, key):
        with self._lock:
            store = self._stores.get(store_name)
            if store is None:
                logger.error(f"Store {store_name} does not exist.")
                return None

            key_data = store.get(key)
            if key_data is None:
                logger.info(f"Key {key} does not exist in store {store_name}.")
                return None

            # Check if the key has expired
            current_time = time.time()
            if 'exp_time' in key_data and current_time > key_data['exp_time']:
                logger.info(f"Key {key} in store {store_name} has expired.")
                return None

            return key_data