#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  haystack.py
#
#  Copyright 2013 David Gloyn-Cox <peregrin@dreffed.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#
import timeit
import datetime
import re

import os
import sys

class haystackFiles(object):
    """ This class will process the files in the haystack folders, we can have several types
        of files in here.
        URL files
    """

    def __init__(self):
        print('Init')
        self._title = 'Haystack'
        self._version = '1.0'
        self._descr = '''Will scroll through the Haystack directory and process the files based on location and type.'''
        self._engine_id = -1
        self._state = 'Initialized'
        self._haystackPath = ''
        self._db = None

    def state(self):
        """ Returns the state of the engine
        """
        return self._state

    def start(self):
        """ starts the engine, and will prepare any special function retquired
            This is the only method that Peregrin will need for it to work with this object.
        """
        self._state = 'Started'

    def run(self, *args, **kwargs):
        """ will process the class and auto run the relevant actions
        """
        self.actions()

        for funcName, action in self._actions.items():
            actionName, actionParams = action
            if actionParams == None:
                func = getattr(self, funcName)
                print('Running %s.%s' % (self._title, funcName))
                func()
            else:
                self.runAction(actionName, funcName)
        self._db.commit_db()

    def runAction(self, actionName, funcName):
        """ will run the action specifiec in the action name
        """
        itemDataList = self._db.getItemDataList(self._engine_id, actionName)
        actionId = self._db.addAction(actionName)
        func = getattr(self, funcName)

        i = 0
        total = len(itemDataList)
        startTime = timeit.default_timer()
        print('%s.%s => %s' % (self._title, funcName, total))

        for itemId, itemURI in itemDataList:
            i += 1
            func(itemURI)
            self._db.updateItem(self._engine_id, itemId, actionId, datetime.datetime.now())

            if i % 1000 == 0:
                interTime = timeit.default_timer()
                step = ((interTime - startTime) / i)
                eta = step * (total - i)
                print('Processing: %s / %s ETA: %ss at %s' % (i, total, eta, step))

                if self._db != None:
                    self._db.commit_db()

        self._db.commit_db()

    def info(self):
        """ returns the objects information
        """
        return (self._title, self._version, self._descr)

    def getId(self):
        return self._engine_id

    def setId(self, Id):
        self._engine_id = Id

    def config(self, config):
        """ pass in the configuration file
        """
        self._config = config
        self._haystackPath = self._config.get('Paths', 'Haystack')

    def close(self):
        self._state = 'Dying'

    def acceptDB(self, db):
        """ if this is declared the calling program will pass in the
        cursor from the exisiting db """
        self._db = db

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions = {}
        self._actions['getItems'] = ('FileCrawler', None)
        #self._actions['getContents'] = ('ParseContents', ('path'))
        return self._actions

    def getItems(self):
        """ Will search the path provided and apply the tags given
          """
        fname = 'getItems'
        actionId = self._db.addAction('WebCrawler')
        actionId_ex = self._db.addAction('extractor')

        if not os.path.exists(self._haystackPath):
            self._haystackPath = os.path.expanduser(self._haystackPath)

        if not os.path.exists(self._haystackPath):
            self._haystackPath = os.path.abspath(self._haystackPath)

        print('\t{0} [{1}]'.format(fname, self._haystackPath))

        for (pathStr, dirs, files) in os.walk(self._haystackPath):
            head, tail = os.path.split(pathStr)
            for fileStr in files:
                fileDTCheck = ''
                filePath = os.path.join(pathStr,fileStr)

                # get the file date...
                fileDT =  datetime.datetime.fromtimestamp(os.path.getmtime(filePath)).replace(microsecond=0)
                fileSize = os.path.getsize(filePath)
                fileName, fileExt = os.path.splitext(filePath)

                # save the item to the database
                itemId = self._db.addItem(self._engine_id, "file://%s" % filePath, fileDT)
                
                # now check the data for this item...
                itemList = self._db.getItemDataAll(itemId) 
                isMatch = False
                for item in itemList:
                    if item[0] == 'FileDate':
                        # we have a date string...
                        fileDTCheck = datetime.datetime.strptime(item[1], "%Y-%m-%d %H:%M:%S")
                        if fileDTCheck == fileDT:
                            # the same time, no changes needed
                            isMatch = True
                
                if isMatch:
                    # get next item as this is already exists
                    continue
                
                # print(the details)
                print(fileDTCheck, fileDT)
                print('>>\t%s\t%s\t%s' % (fname, head, tail))
            
                # set the datetime and other details
                self._db.addItemData(itemId, 'Haystack', tail, 0)
                self._db.addItemData(itemId, 'FileName', fileName, 0)
                self._db.addItemData(itemId, 'FileExt', fileExt, 0)
                self._db.addItemData(itemId, 'FileDate', fileDT, 0)
                self._db.addItemData(itemId, 'FileSize', fileSize, 0)

                # now to process the file...
                # this will extract out metadata and add to the itemData table the value pairs.
                pattern = re.compile(r'^.*[.](?P<ext>htm|html)$')
                pattPNG = re.compile(r'^.*[.](?P<ext>mp.|mpeg|avi|swf|jpg|jpeg|png)$')
                pattTAR = re.compile(r'^.*[.](?P<ext>tar\.gz|tar\.bz2|\.zip|\.tar|\.7z)$')

                m = pattern.match(filePath)
                if not m:
                    m = pattPNG.match(filePath)

                if not m:
                    m = pattTAR.match(filePath)

                if not m:
                    self.getContents(itemId, filePath, tail)
                    self._db.updateItem(self._engine_id, itemId, actionId_ex, datetime.datetime.now())

                else:
                    # we have a file extension...
                    if m.group('ext').startswith('.htm'):
                        # add this as an event to be processed by the html link reader...
                        self._db.addItemEvent(self._engine_id, actionId, itemId)

        if self._db:
            self._db.commit_db()


    def getContents(self, itemId, itemURI, *args):
        """ Will process the file, expected files are text and URL bookmarks...
                This will handle:
                    Single URL no markup
                    internet shortcut file
                    Firefox bookmark export
        """
        if args:
            actionId = self._db.addAction(args[0])       
        else:
            actionId = -1

        print('\t\t[%s] %s\t(%s)' % (itemId, itemURI, actionId))
            
        # dissect the file
        patURL = re.compile(r'URL=(?P<url>.*$)', re.IGNORECASE)
        patHttp = re.compile(r'(?P<url>http.*$)', re.IGNORECASE)
        patFtp = re.compile(r'(?P<url>ftp.*$)', re.IGNORECASE)

        f = open(itemURI,"r")
        url = ''
        idx = -1

        for line in f:
            idx += 1
            m = patURL.match(line)
            if not m:
                m = patHttp.match(line)

            if not m:
                m = patFtp.match(line)

            if m:
                url =  m.group('url')
                itemIdRight = self._db.addItem(self._engine_id, url, datetime.datetime.now(), args)
                self._db.addItemLink(self._engine_id, itemId, itemIdRight, 'Contains')
                
                # we have a URI, down we wnat to action it, use the tail value to set the action:
                self._db.addItemEvent(self._engine_id, actionId, itemIdRight)

            self._db.addItemData(itemId, 'Contents', line, idx)


def main():
    import imp
    import inspect
    import configparser

    # the following is a hack to allow me to load mods and classes from a filepath
    modPath = os.path.dirname(__file__)
    corepath = os.path.split(modPath)[0]
    filepath = os.path.join(corepath, 'db', 'PeregrinDB.py')
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
    
    py_mod = imp.load_source(mod_name, filepath)
    classmembers = inspect.getmembers(py_mod, inspect.isclass)
    for cls in classmembers:
        my_class = getattr(py_mod, cls[0])
        if hasattr(my_class, 'connect_db'):
            db = cls[1]()
            break

    print('Running >> %s' % datetime.datetime.today())

    # configuration details
    cfg_path = os.path.join(corepath, 'config', 'PeregrinDaemon.cfg')
    config = configparser.RawConfigParser()
    config.readfp(open(cfg_path))

    # database, details in the config file
    db.connect_db(config)

    # create the object
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)

    # open the first class found...    
    obj = classes[0][1]()
    obj.config(config)

    obj.acceptDB(db)
    obj._engine_id = obj._db.addEngine(obj._title, obj._version, obj._descr)

    obj.start()
    print('Engine:\t%s (%s)\t[%s]' % (obj._title, obj._version, obj._engine_id))

    print(obj.info())
    print(obj.actions())
    obj.run()

    del obj
    
    print('Ending >> %s' % datetime.datetime.today())
    print('================================================')
    
    return 0

if __name__ == '__main__':
    main()

