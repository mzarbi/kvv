import logging

import Pyro4
from cryptography.fernet import Fernet

from plugins import StoreDefinitionMixin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('remote_proxies')

STORE_NAME = "secrets"
@Pyro4.expose
class SecretsPlugin:
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.create_store(STORE_NAME)
        self.cipher_suite = Fernet(self._resolve_key())

    def _resolve_key(self):
        # encryption_key = Fernet.generate_key()
        # Resolve encryption key using cyberark
        return b'NBmku5ZLhKGlclqxJBaHujx5PTptxrDzQugGx_ZJHc0='

    def add_confidential_key(self, key, value, ttl=None, readonly=False):
        """Encrypts and adds a confidential key to the store."""
        encrypted_value = self.cipher_suite.encrypt(value.encode())
        self._add_key(STORE_NAME, key, value=encrypted_value, ttl=ttl, readonly=readonly)

    def get_confidential_key(self, key):
        """Retrieves and decrypts a confidential key from the store."""
        encrypted_value = self._get_key(STORE_NAME, key)
        if encrypted_value:
            decrypted_value = self.cipher_suite.decrypt(encrypted_value)
            return decrypted_value.decode()
        return None
