# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
#           invalid constant name convention
"""

@project: Peregrin (Haystack)
@author: david gloyn-cox
"""
import os
from engines import peregrinbase

class RSSFeed(peregrinbase.PeregrinBase):
    """This will read an RSS feed and save the data to
    Peregrin DB"""
    def __init__(self):
        super().__init__()
        self._title = 'RSS Reader'
        self._version = '0.1'
        self._descr = 'RSS Reader class for Peregrin.'
        self._engine_id = -1
        self._state = 'Initialized'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions['getItems'] = ('search', None)

        return self._actions

    def getItems(self, uri):
        pass

if __name__ == '__main__':
    import sys

    loader_config = {}
    modPath = os.path.dirname(__file__)
    loader_config['path'] = os.path.split(modPath)[0]
    loader_config['name'] = 'RSSFeed'
    loader_config['module'] = sys.modules[__name__]

    loader_config['db'] = {}
    loader_config['db']['path'] = 'db'
    loader_config['db']['name'] = 'PeregrinDB.py'

    loader_config['config'] = {}
    loader_config['config']['path'] = 'config'
    loader_config['config']['name'] = 'PeregrinDaemon.cfg'

    peregrinbase.main(loader_config)
