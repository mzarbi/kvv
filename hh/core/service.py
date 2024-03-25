from abc import ABC, abstractmethod
from functools import wraps
import threading


# Synchronization Decorator
def synchronized(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)

    return wrapper


# Abstract Service Class
class AbstractService(ABC):
    def __init__(self):
        self._lock = threading.Lock()

    def shutdown(self):
        pass
