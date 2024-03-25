import os
import signal
import socket
import ssl
import threading
import time

import msgpack
from concurrent.futures import ThreadPoolExecutor
import yaml
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('RemoteObjectServer')


class RemoteObjectServer:
    def __init__(self, max_workers=10, refresh_interval=10, use_ssl=False, certfile=None, keyfile=None):
        self.services = {}
        self.running = True
        self.last_modified_time = None
        self.refresh_interval = refresh_interval

        self.use_ssl = use_ssl
        self.certfile = certfile
        self.keyfile = keyfile
        self.refresh_thread = None
        self.shutdown_event = threading.Event()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.config_file = ".services"
        self.load_services()

    def is_valid_service_config(self, service_config):
        """Validate service configuration."""
        required_keys = {'module', 'class'}
        return all(key in service_config for key in required_keys)

    def load_services(self):
        """Load or reload services from the YAML configuration file if there are changes."""
        try:
            modified_time = os.path.getmtime(self.config_file)
            if modified_time == self.last_modified_time:
                return  # No changes to the configuration file.

            self.last_modified_time = modified_time

            with open(self.config_file, 'r') as file:
                config = yaml.safe_load(file)
                for uri, details in config.get('services', {}).items():
                    if not self.is_valid_service_config(details):
                        logger.error(f"Invalid configuration for service {uri}.")
                        continue

                    module = importlib.import_module(details['module'])
                    cls = getattr(module, details['class'])
                    self.register_service(uri, cls())
                    logger.info(f"Service {uri} loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load services: {e}")

    def register_service(self, uri, service_instance):
        self.services[uri] = service_instance
        logger.info(f"Registered service {uri}.")

    def handle_client(self, client_socket):
        while self.running:
            try:
                raw_length = client_socket.recv(4)
                if not raw_length:
                    logger.warning("Client may have disconnected.")
                    break

                msg_length = int.from_bytes(raw_length, byteorder='big')
                data = client_socket.recv(msg_length)
                if not data:
                    logger.warning("Failed to read message data. Client may have disconnected.")
                    break

                uri, method_name, args, kwargs = msgpack.unpackb(data, raw=False)

                service = self.services.get(uri)
                if not service:
                    raise KeyError(f"Service {uri} not found")

                method = getattr(service, method_name, None)
                if not method:
                    raise AttributeError(f"Method {method_name} not found in service {uri}")

                logger.debug(f"Received request for {uri}.{method_name}.")
                result = method(*args, **kwargs)
                response = msgpack.packb(result, use_bin_type=True)
                client_socket.sendall(len(response).to_bytes(4, byteorder='big') + response)
            except KeyError as e:
                logger.error(f"Service error: {e}")
            except AttributeError as e:
                logger.error(f"Method error: {e}")
            except Exception as e:
                logger.error(f"Error handling client request: {e}")
                break

    def start_server(self, host, port):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(5)
        logger.info(f"Server listening on {host}:{port}")

        self.refresh_thread = threading.Thread(target=self.refresh_services, daemon=True)
        self.refresh_thread.start()

        signal.signal(signal.SIGINT, self.graceful_shutdown)
        signal.signal(signal.SIGTERM, self.graceful_shutdown)

        context = None
        if self.use_ssl:
            if not self.certfile or not self.keyfile:
                logger.error("SSL is enabled but certificate or key file is missing.")
                return
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.certfile, keyfile=self.keykeyfile)

        try:
            while self.running:
                try:
                    client_socket, _ = self.server_socket.accept()
                    if self.use_ssl and context:
                        client_socket = context.wrap_socket(client_socket, server_side=True)
                except socket.timeout:
                    continue
                except socket.error:
                    continue  # To handle the interrupt on accept

                logger.debug("Accepted connection from client.")
                self.executor.submit(self.handle_client, client_socket)
        finally:
            self.server_socket.close()
            self.executor.shutdown(wait=True)
            self.refresh_thread.join()
            logger.info("Server shutdown complete.")

    def graceful_shutdown(self, signum, frame):
        logger.info("Shutdown signal received, shutting down gracefully...")
        self.shutdown_event.set()
        self.server_socket.close()
        self.running = False

        for uri, instance in self.services.items():
            if hasattr(instance, 'shutdown'):
                logger.info(f"Service {uri} is shutting down")
                instance.shutdown()
                logger.info(f"Service {uri} shutdown complete.")

    def refresh_services(self):
        """Periodically refresh services, but wait efficiently using an event."""
        while not self.shutdown_event.is_set():
            logger.info("Refreshing services...")
            self.load_services()
            # Wait for the refresh interval or until a shutdown is initiated
            self.shutdown_event.wait(self.refresh_interval)