import os
import sys
import unittest

import cherrypy
from mock import patch, MagicMock as Mock

sys.path += [os.path.realpath( '..'), os.path.realpath('.')] + sys.path

from server import server_restart


class ServerRestartTests(unittest.TestCase):
    @patch.object(cherrypy.engine, 'restart')
    def test_cherrypy_restart_called(self, restart_method):
        server_restart('cherrypy')

        restart_method.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
