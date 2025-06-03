import unittest
import os
import sys

# Add project root to sys.path to allow imports from aisans package
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from aisans.indexer.indexer import Indexer

class TestIndexerConfig(unittest.TestCase):

    def test_default_db_path(self):
        """Test that Indexer uses 'aisans_index.db' by default."""
        db_name = 'aisans_index.db'
        old_env_var = os.environ.pop('AISANS_DB_PATH', None)

        # Ensure the default DB does not exist before test
        if os.path.exists(db_name):
            os.remove(db_name)

        indexer = Indexer()
        self.addCleanup(indexer.close)
        # Indexer creates the db on init, so it should exist for removal
        self.addCleanup(self._remove_if_exists, db_name)

        try:
            self.assertEqual(indexer.db_path, db_name)
            self.assertTrue(os.path.exists(db_name), "Database file should be created by Indexer.")
        finally:
            if old_env_var is not None:
                os.environ['AISANS_DB_PATH'] = old_env_var

    def test_env_var_db_path(self):
        """Test that Indexer uses the path from AISANS_DB_PATH environment variable."""
        db_name = 'test_env_indexer.db'
        original_env_value = os.environ.get('AISANS_DB_PATH')
        os.environ['AISANS_DB_PATH'] = db_name

        # Ensure the env DB does not exist before test
        if os.path.exists(db_name):
            os.remove(db_name)

        indexer = Indexer()
        self.addCleanup(indexer.close)
        self.addCleanup(self._remove_if_exists, db_name)

        try:
            self.assertEqual(indexer.db_path, db_name)
            self.assertTrue(os.path.exists(db_name), "Database file should be created by Indexer.")
        finally:
            # Restore or remove the environment variable
            if original_env_value is None:
                del os.environ['AISANS_DB_PATH']
            else:
                os.environ['AISANS_DB_PATH'] = original_env_value


    def test_constructor_override_db_path(self):
        """Test that constructor db_path overrides AISANS_DB_PATH environment variable."""
        constructor_db_name = 'constructor_test.db'
        env_db_name = 'env_should_be_ignored.db'

        original_env_value = os.environ.get('AISANS_DB_PATH')
        os.environ['AISANS_DB_PATH'] = env_db_name

        # Ensure constructor DB and ignored ENV DB do not exist before test
        if os.path.exists(constructor_db_name):
            os.remove(constructor_db_name)
        if os.path.exists(env_db_name):
            os.remove(env_db_name)

        indexer = Indexer(db_path=constructor_db_name)
        self.addCleanup(indexer.close)
        self.addCleanup(self._remove_if_exists, constructor_db_name)
        # Also schedule cleanup for the env_db_name, though it shouldn't be created
        self.addCleanup(self._remove_if_exists, env_db_name)

        try:
            self.assertEqual(indexer.db_path, constructor_db_name)
            self.assertTrue(os.path.exists(constructor_db_name), "Constructor DB file should be created.")
            self.assertFalse(os.path.exists(env_db_name), "Environment variable DB file should NOT be created.")
        finally:
            # Restore or remove the environment variable
            if original_env_value is None:
                del os.environ['AISANS_DB_PATH']
            else:
                os.environ['AISANS_DB_PATH'] = original_env_value

    def _remove_if_exists(self, filepath):
        """Helper to remove a file if it exists."""
        if os.path.exists(filepath):
            # Try to remove the main db file
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Warning: Could not remove file {filepath}: {e}")

            # SQLite may create journal files or WAL files, attempt to remove common ones
            common_suffixes = ['-journal', '-wal', '-shm']
            for suffix in common_suffixes:
                try:
                    journal_file = filepath + suffix
                    if os.path.exists(journal_file):
                        os.remove(journal_file)
                except OSError as e:
                    print(f"Warning: Could not remove journal file {journal_file}: {e}")


if __name__ == '__main__':
    unittest.main()
