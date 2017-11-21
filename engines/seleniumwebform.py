# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
#           invalid constant name convention
"""
@title: Selenium Web Driver - Form / Result submission
@purpose: Will open a URL, select the specified form
fill in fields, submit
For the results panel will select entries (Class select)
for each entry extract key data and post to Haystack
Will read entries from haystack and then extract further pages.
@project: Peregrin (Haystack)
@author: david gloyn-cox
@created: 2017-11-20
"""
import os
from engines import peregrinbase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

class SeleniumWebForm(peregrinbase.PeregrinBase):
    """This will read an RSS feed and save the data to
    Peregrin DB"""
    def __init__(self):
        super().__init__()
        self._title = 'Selenium Web Form and Result Reader'
        self._version = '0.1'
        self._descr = 'Selenium class for Peregrin.'
        self._engine_id = -1
        self._state = 'Initialized'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions['getItems'] = ('search', None)

        return self._actions

    def getItems(self):
        pass

    def getResults(self, uri):
        pass

if __name__ == '__main__':
    import sys

    config_data = {}
    modPath = os.path.dirname(__file__)
    config_data['path'] = os.path.split(modPath)[0]
    config_data['name'] = 'SeleniumWebForm'
    config_data['module'] = sys.modules[__name__]

    config_data['db'] = {}
    config_data['db']['path'] = 'db'
    config_data['db']['name'] = 'PeregrinDB.py'

    config_data['config'] = {}
    config_data['config']['path'] = 'config'
    config_data['config']['name'] = 'PeregrinDaemon.cfg'

    #load class specific items...
    cls_name = 'SeleniumWebForm'
    config_data[cls_name] = {}
    config_data[cls_name]['uri'] = 'http://www.bctechnology.com/jobs/search.cfm'
    config_data[cls_name]['data'] = []

    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'business intelligence', 'id': 0})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'database', 'id': 1})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'project management', 'id': 2})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'software engineer', 'id': 3})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'strategic', 'id': 4})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'business analysis', 'id': 5})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'software selection', 'id': 6})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'erp implementation', 'id': 7})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'system integration', 'id': 8})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'quality assurance', 'id': 9})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'User experience UX', 'id': 10})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'data dataops', 'id': 11})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'dev ops devops', 'id': 12})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'fun energetic', 'id': 13})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'project coordination', 'id': 14})
    config_data[cls_name]['data'].append({'name': 'keyword', 'value': 'salesforce', 'id': 15})

    func_name = 'getItems'
    config_data[cls_name][func_name] = {}
    config_data[cls_name][func_name]['form'] = {
            'name': 'frm1', 
            'formfields': [{'id': 'keyword', 'values': '{data:keyword}'}]}
    config_data[cls_name][func_name]['results'] = {
            'result':{
                'type': 'selector',
                'name': 'class',
                'value': 'darkgold',
                'map':[
                        {'name': 'href', 
                        'value': '{params:showid}', 
                        'type':  'url',
                        'label': 'JobId'},
                        {'name': 'title', 
                        'type':  'attr',
                        'label': 'JobTitle'}
                        ],
                'check':[
                    {'type':'attr', 
                    'name':'id', 
                    'value': 'job-title-link'}
                    ]
                },
            'nextlink': {'text': 'Next ', 'type': 'a'}
        }

    func_name = 'getResults'
    config_data[cls_name][func_name] = {}

    peregrinbase.main(config_data)
