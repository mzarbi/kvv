import unittest
from unittest.mock import patch
from cryptography.fernet import Fernet

from plugins.sensitive import SecretsPlugin
from store import AbstractKVStore


class ConfidentialStoreMixin(AbstractKVStore, SecretsPlugin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        SecretsPlugin.__init__(self, *args, **kwargs)


class TestConfidentialStoreMixin(unittest.TestCase):
    def setUp(self):
        # Use a fixed key for unit testing purposes.
        test_key = b'NBmku5ZLhKGlclqxJBaHujx5PTptxrDzQugGx_ZJHc0='
        self.cipher_suite = Fernet(test_key)

        # Initialize EnhancedKVStore with ConfidentialStoreMixin functionality
        self.kv_store = ConfidentialStoreMixin(backup_dir="test_backups")
        self.kv_store.start_tasks()

    def test_add_and_get_confidential_key(self):
        # Test that a confidential key can be added and then retrieved correctly.
        test_key = "confidential_key"
        test_value = "super_secret_value"
        self.kv_store.add_confidential_key(test_key, test_value)

        retrieved_value = self.kv_store.get_confidential_key(test_key)
        self.assertEqual(retrieved_value, test_value,
                         "The retrieved value should match the original confidential value.")

    def test_encryption_decryption(self):
        # Test to ensure the value is actually encrypted in storage and decrypted on retrieval.
        test_key = "another_confidential_key"
        test_value = "another_super_secret_value"
        self.kv_store.add_confidential_key(test_key, test_value)

        # Directly retrieve the encrypted value from the store to inspect it.
        encrypted_value = self.kv_store._get_key("secrets", test_key)
        self.assertNotEqual(encrypted_value, test_value.encode(),
                            "Stored value should be encrypted and different from the original.")

        # Now retrieve it using the provided method to ensure it's decrypted back.
        decrypted_value = self.kv_store.get_confidential_key(test_key)
        self.assertEqual(decrypted_value, test_value, "Decrypted value should match the original.")


if __name__ == '__main__':
    unittest.main()
