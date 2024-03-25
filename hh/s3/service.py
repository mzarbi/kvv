import threading
import time
import boto3
from core.service import AbstractService, synchronized


class S3FileManager(AbstractService):
    def __init__(self, bucket_name, polling_interval=300):
        """
        Initializes a new instance of S3FileManager to manage and poll files from an S3 bucket.

        Parameters:
            bucket_name (str): The name of the S3 bucket to manage.
            polling_interval (int): The interval, in seconds, at which to poll the S3 bucket for new files.
        """
        super().__init__()
        self.bucket_name = bucket_name
        self.polling_interval = polling_interval
        self.files = {}
        self.shutdown_event = threading.Event()
        self.s3_client = boto3.client('s3')
        self.poll_thread = threading.Thread(target=self._poll_s3, daemon=True)
        self.poll_thread.start()

    @synchronized
    def fetch_paths(self, prefix=''):
        """
        Fetches a list of paths from the S3 bucket that match the given prefix.

        Parameters:
            prefix (str): The prefix to filter paths by.

        Returns:
            list: A list of paths that match the given prefix.
        """
        # Use the cached files if fetching by prefix
        return [path for path in self.files.keys() if path.startswith(prefix)]

    def _poll_s3(self):
        """
        Periodically polls the S3 bucket for the list of files, updating the local cache.
        This method runs in a separate thread.
        """
        while not self.shutdown_event.is_set():
            try:
                paginator = self.s3_client.get_paginator('list_objects_v2')
                page_iterator = paginator.paginate(Bucket=self.bucket_name)

                new_files = {}
                for page in page_iterator:
                    for obj in page.get('Contents', []):
                        new_files[obj['Key']] = obj['LastModified']

                self.files = new_files
            except Exception as e:
                print(f"Error polling S3 bucket: {e}")

            # Wait for the next poll interval or until shutdown is initiated
            self.shutdown_event.wait(self.polling_interval)

    def shutdown(self):
        """
        Initiates the shutdown process for the polling thread, ensuring a graceful termination.
        """
        self.shutdown_event.set()
        self.poll_thread.join()
