from core.service import AbstractService, synchronized


class NASPathManager(AbstractService):
    def __init__(self):
        super().__init__()
        self.paths = {}

    @synchronized
    def add_path(self, label, env, os, path):
        """
        Adds or updates a NAS path.
        """
        if label not in self.paths:
            self.paths[label] = {}
        if env not in self.paths[label]:
            self.paths[label][env] = {}
        self.paths[label][env][os] = path

    @synchronized
    def get_path(self, label, env, os):
        """
        Retrieves a NAS path using label, env, and os.
        """
        try:
            return self.paths[label][env][os]
        except KeyError:
            return None  # Or raise a more specific error if that's preferred

    @synchronized
    def remove_path(self, label, env, os):
        """
        Removes a specified NAS path.
        """
        try:
            del self.paths[label][env][os]
            if not self.paths[label][env]:
                del self.paths[label][env]  # Clean up if no OS entries remain
            if not self.paths[label]:
                del self.paths[label]  # Clean up if no env entries remain
        except KeyError:
            pass  # Ignore if the path does not exist

    @synchronized
    def list_paths(self):
        """
        Lists all paths with their labels, environments, and operating systems.
        """
        return {label: {env: {os: path for os, path in os_paths.items()}
                for env, os_paths in envs.items()} for label, envs in self.paths.items()}
