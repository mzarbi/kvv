import unittest

from nas import NASPathManager


class TestNASPathManager(unittest.TestCase):
    def setUp(self):
        """Initialize a new NASPathManager for each test."""
        self.manager = NASPathManager()

    def test_add_and_get_path(self):
        """Test adding a path and retrieving it."""
        self.manager.add_path('project1', 'dev', 'linux', '/dev/linux/project1')
        self.assertEqual(self.manager.get_path('project1', 'dev', 'linux'), '/dev/linux/project1')

    def test_get_path_nonexistent(self):
        """Test retrieving a path that doesn't exist."""
        self.assertIsNone(self.manager.get_path('nonexistent', 'dev', 'linux'))

    def test_remove_path(self):
        """Test removing an existing path."""
        self.manager.add_path('project2', 'dev', 'linux', '/dev/linux/project2')
        self.manager.remove_path('project2', 'dev', 'linux')
        self.assertIsNone(self.manager.get_path('project2', 'dev', 'linux'))

    def test_remove_nonexistent_path(self):
        """Test removing a path that doesn't exist."""
        # This should not raise an error
        self.manager.remove_path('nonexistent', 'dev', 'linux')

    def test_list_paths(self):
        """Test listing all paths."""
        self.manager.add_path('project1', 'dev', 'linux', '/dev/linux/project1')
        self.manager.add_path('project2', 'stg', 'windows', '/stg/windows/project2')
        expected_paths = {
            'project1': {'dev': {'linux': '/dev/linux/project1'}},
            'project2': {'stg': {'windows': '/stg/windows/project2'}}
        }
        self.assertEqual(self.manager.list_paths(), expected_paths)

if __name__ == '__main__':
    unittest.main()
