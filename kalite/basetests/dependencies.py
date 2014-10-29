import logging
import unittest


class SqliteTests(unittest.TestCase):

    def test_sqlite_is_installed(self):
        logging.info("Testing SQLite3 is installed...")
        self.assertEqual(True, False)

    def test_sqlite_version(self):
        logging.info("Testing SQLite3 version...")
        self.assertEqual(True, False)


class DjangoTests(unittest.TestCase):

    def test_django_is_installed(self):
        logging.info("Testing Django is installed...")
        self.assertEqual(True, False)

    def test_django_version(self):
        logging.info("Testing Django version...")
        self.assertEqual(True, False)


class PackageTests(unittest.TestCase):

    def test_packages_are_installed(self):
        logging.info("Testing required Python packages are installed...")
        self.assertEqual(True, False)

    def test_packages_version(self):
        logging.info("Testing required Python packages versions...")
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
