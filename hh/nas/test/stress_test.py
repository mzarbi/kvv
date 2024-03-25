import threading
from core.client import RemoteObjectClient
import random
import string


def perform_operations(client_id):
    with RemoteObjectClient('127.0.0.1', 65432, "NASPathManager") as path_manager:
        try:
            project = f"project{client_id}"
            environment = random.choice(["dev", "prd"])
            os = random.choice(["linux", "windows"])
            path = f"/nas/{environment}/{os}/{project}"

            # Add a path
            path_manager.add_path(project, environment, os, path)
            print(f"Client {client_id}: Added {path}")

            # Get and print the path
            retrieved_path = path_manager.get_path(project, environment, os)
            print(f"Client {client_id}: Retrieved {path} -> {retrieved_path}")

            # Remove the path
            path_manager.remove_path(project, environment, os)
            print(f"Client {client_id}: Removed {path}")

        except Exception as e:
            print(f"Client {client_id}: An error occurred: {e}")


def stress_test(num_clients=50):
    threads = []
    for i in range(num_clients):
        thread = threading.Thread(target=perform_operations, args=(i,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()


if __name__ == "__main__":
    stress_test()
