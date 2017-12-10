import unittest
from unittest.mock import patch, mock_open
import os

from amazon_dash.exceptions import SecurityException, InvalidConfig
from pyfakefs.fake_filesystem_unittest import Patcher
from amazon_dash.config import Config, only_root_write, oth_w_perm

__dir__ = os.path.abspath(os.path.dirname(__file__))
config_data = open(os.path.join(__dir__, 'fixtures', 'config.yml')).read()



class FileMockBase(object):
    def setUp(self):
        self.patcher = Patcher()
        self.patcher.setUp()
        self.file = 'config.yml'
        self.patcher.fs.CreateFile(self.file)

    def tearDown(self):
        self.patcher.tearDown()


class TestConfig(unittest.TestCase):

    @patch('os.path.lexists')
    def test_not_found(self, mock_method):
        with self.assertRaises(FileNotFoundError):
            Config('config.yml')
        mock_method.assert_called_once()

    @patch('os.getuid', return_value=1000)
    def test_other_user(self, getuid_mock):
        file = 'amazon-dash.yml'
        with Patcher() as patcher:
            patcher.fs.CreateFile(file, contents=config_data)
            os.chown(file, 1000, 1000)
            os.chmod(file, 0o660)
            Config(file)
        patcher.tearDown()

    @patch('os.getuid', return_value=1000)
    def test_other_user_error(self, getuid_mock):
        file = 'amazon-dash.yml'
        with Patcher() as patcher:
            patcher.fs.CreateFile(file, contents=config_data)
            os.chown(file, 1000, 1000)
            os.chmod(file, 0o666)
            with self.assertRaises(SecurityException):
                Config(file)
        patcher.tearDown()

    @patch('os.getuid', return_value=0)
    def test_root(self, getuid_mock):
        file = 'amazon-dash.yml'
        with Patcher() as patcher:
            patcher.fs.CreateFile(file, contents=config_data)
            os.chown(file, 0, 0)
            os.chmod(file, 0o660)
            Config(file)
        patcher.tearDown()

    @patch('os.getuid', return_value=0)
    def test_root(self, getuid_mock):
        file = 'amazon-dash.yml'
        with Patcher() as patcher:
            patcher.fs.CreateFile(file, contents=config_data)
            os.chown(file, 1000, 1000)
            os.chmod(file, 0o660)
            with self.assertRaises(SecurityException):
                Config(file)
        patcher.tearDown()

    @patch('os.getuid', return_value=1000)
    def test_invalid_config(self, getuid_mock):
        file = 'amazon-dash.yml'
        with Patcher() as patcher:
            patcher.fs.CreateFile(file, contents='invalid config')
            os.chown(file, 1000, 1000)
            os.chmod(file, 0o660)
            with self.assertRaises(InvalidConfig):
                Config(file)


class TestOthWPerm(FileMockBase, unittest.TestCase):
    def test_perms(self):
        os.chmod(self.file, 0o666)
        self.assertTrue(oth_w_perm(self.file))

    def test_no_perms(self):
        os.chmod(self.file, 0o660)
        self.assertFalse(oth_w_perm(self.file))


class TestOnlyRootWrite(FileMockBase, unittest.TestCase):

    def test_root_owner(self):
        os.chown(self.file, 0, 0)
        os.chmod(self.file, 0o660)
        self.assertTrue(only_root_write(self.file))

    def test_no_perms(self):
        os.chown(self.file, 1000, 1000)
        os.chmod(self.file, 0o000)
        self.assertTrue(only_root_write(self.file))

    def test_other_perms(self):
        os.chown(self.file, 0, 0)
        os.chmod(self.file, 0o666)
        self.assertFalse(only_root_write(self.file))

    def test_user_owner(self):
        os.chown(self.file, 1000, 1000)
        os.chmod(self.file, 0o660)
        self.assertFalse(only_root_write(self.file))

