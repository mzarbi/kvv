import logging
import Pyro4
from plugins import StoreDefinitionMixin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

STORE_NAME = "paths"


@Pyro4.expose
class PathManagementMixin(StoreDefinitionMixin):
    def __init__(self, *args, **kwargs):
        self.create_store(STORE_NAME)

    def add_or_update_path(self, label, env, system, path):
        # Fetch existing paths data or initialize it if it doesn't exist
        paths_data = self._get_key(STORE_NAME, label) or {}

        # Update or add the new path within the nested dictionary structure
        if env not in paths_data:
            paths_data[env] = {}
        paths_data[env][system] = path

        # If the label does not exist, use _add_key; otherwise, use _edit_key
        if not paths_data:
            self._add_key(STORE_NAME, label, value=paths_data)
        else:
            self._edit_key(STORE_NAME, label, value=paths_data)

    def get_path(self, label, env, system):
        paths_data = self._get_key(STORE_NAME, label)
        if paths_data:
            return paths_data.get(env, {}).get(system)
        return None

    def update_paths_object(self, label, new_paths):
        self._edit_key(STORE_NAME, label, value=new_paths)

    def edit_specific_path(self, label, env, system, new_path):
        self.add_or_update_path(label, env, system, new_path)

    def get_all_paths(self):
        store_data = self._get_all_keys(STORE_NAME)
        return store_data if store_data else {}
