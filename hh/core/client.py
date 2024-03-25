import socket
import ssl

import msgpack
import logging

# Configure logging for the client
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger('RemoteObjectClient')


class ServiceProxy:
    """Proxy for a specific remote service."""

    def __init__(self, client, service_uri):
        self.client = client
        self.service_uri = service_uri

    def __getattr__(self, method_name):
        def remote_method(*args, **kwargs):
            result = self.client.call_service(self.service_uri, method_name, *args, **kwargs)
            logger.debug(f"Method {method_name} called on {self.service_uri} with args: {args} and kwargs: {kwargs}")
            return result

        return remote_method


class RemoteObjectClient:
    def __init__(self, host, port, service_uri, use_ssl=False, server_cert=None):
        self.host = host
        self.port = port
        self.service_uri = service_uri
        self.sock = None
        self.use_ssl = use_ssl
        self.server_cert = server_cert
        logger.info(f"Initialized client for service URI: {service_uri} at {host}:{port}")

    def __enter__(self):
        self.sock = socket.create_connection((self.host, self.port))
        if self.use_ssl:
            context = ssl.create_default_context()
            if self.server_cert:
                context.load_verify_locations(self.server_cert)
            else:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE  # Be cautious with this in production
            self.sock = context.wrap_socket(self.sock, server_hostname=self.host)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sock:
            self.sock.close()
            logger.info("Connection closed.")
            self.sock = None

    def __getattr__(self, method_name):
        def remote_method(*args, **kwargs):
            result = self.call_service(self.service_uri, method_name, *args, **kwargs)
            return result

        return remote_method

    def call_service(self, service_uri, method_name, *args, **kwargs):
        if not self.sock:
            logger.error("Attempted to call service without an active session.")
            raise RuntimeError("Session not started. Please use the client within a 'with' context.")

        try:
            request_data = msgpack.packb((service_uri, method_name, args, kwargs), use_bin_type=True)
            self.sock.sendall(len(request_data).to_bytes(4, byteorder='big') + request_data)
            logger.debug(f"Request sent for {service_uri}.{method_name} with args: {args} and kwargs: {kwargs}")

            response_length_bytes = self.sock.recv(4)
            if not response_length_bytes:
                raise ConnectionError("Failed to receive response length from server.")
            response_length = int.from_bytes(response_length_bytes, byteorder='big')

            response_data = b''
            while len(response_data) < response_length:
                part = self.sock.recv(response_length - len(response_data))
                if not part:
                    raise ConnectionError("Connection closed by server before full response was received.")
                response_data += part

            result = msgpack.unpackb(response_data, raw=False)
            logger.debug("Response received.")
            return result
        except Exception as e:
            logger.error(f"Error during service call: {e}")
            raise
