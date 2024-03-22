import logging
import signal

import Pyro4
from store import AbstractKVStore
from plugins.internals import InternalKVStoreMixin
from plugins.secrets import ConfidentialStoreMixin


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')


class EnhancedKVStore(InternalKVStoreMixin, ConfidentialStoreMixin, AbstractKVStore):
    pass


def start_server(host="localhost", port=6666, use_backup=False):
    storage = EnhancedKVStore(
        collect_metrics=True,
        backup_dir="test_backups",
        metrics_interval=60,
        use_backup=use_backup
    )
    storage.start_tasks()

    daemon = Pyro4.Daemon(host=host, port=port)
    uri = daemon.register(storage, objectId="key_value_store")
    logger.info(f"Service started. Object uri = {uri}")

    def signal_handler(sig, frame):
        logger.info('Signal received, shutting down...')
        storage.shutdown()
        daemon.shutdown()
        logger.info("Server has been shut down.")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        daemon.requestLoop()
    finally:
        daemon.close()


if __name__ == "__main__":
    start_server()
