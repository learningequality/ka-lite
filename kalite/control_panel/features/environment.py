"""
environment.py defines setup and teardown behaviors for behave tests.
The behavior in this file is appropriate for integration tests, and
could be used to bootstrap other integration tests in our project.
It sets up a test server and test database by using the LiveServerTestCase
machinery.
"""
from kalite.testing.base_environment import *
