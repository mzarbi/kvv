# Example usage
from core.client import RemoteObjectClient

if __name__ == "__main__":

    with RemoteObjectClient('127.0.0.1', 65432, "NASPathManager") as path_manager:
        try:
            path_manager.add_path("projectX", "dev", "linux", "/nas/dev/linux/projectX")
            path_manager.add_path("projectY", "prd", "windows", "/nas/prd/windows/projectY")

            print(path_manager.get_path("projectX", "dev", "linux"))  # Output: /nas/dev/linux/projectX

            # Remove a path
            path_manager.remove_path("projectX", "dev", "linux")

            # Attempt to retrieve the removed path
            print(path_manager.get_path("projectX", "dev", "linux"))
        except Exception as e:
            print(f"An error occurred: {e}")