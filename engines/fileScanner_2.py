# -*- coding: utf-8 -*-
"""
Created on Sat Jul 20 22:04:06 2013

@author: david
"""

import timeit

import datetime
import os
import sys

import hashlib

import time
import random

class fileScanner(object):
    """ this class will open the BC Tech net site, obtained via ItemData(<engine title>)
        it will then perform a series of keyword searches, keyword are obtained from the ItemId->itemData(keywords)
    """

    def __init__(self):
        print 'Init'
        self._title = 'FileScanner'
        self._version = '2.0'
        self._descr = 'File scanner for .'
        self._engineId = -1
        self._state = 'Initialized'
        self._uri = ''
        self._itemId = 0
        self._db = None
        self.useDelay = False

    def state(self):
        """ Returns the state of the engine
        """
        return self._state

    def start(self):
        """ starts the engine, and will prepare any special function retquired
            This is the only method that Peregrin will need for it to work with this object.
            Will query the database for an entry in the ItemData table and return an URL
            from the ItemURL...
        """
        self._state = 'Started'
        self._itemId = self._db.getItemData(self._title)
        if self._itemId <= 0:
            # missing value need to add it in...
            itemURI = '/home'
            self._itemId = self._db.addItem(self._engineId, itemURI, datetime.datetime.now())
            self._db.addItemData(self._itemId, self._title, itemURI, 0)

            # also set up the default keywords...
            self._db.addItemData(self._itemId, 'folderPaths', '/home/david', 0)
            self._db.addItemData(self._itemId, 'folderPaths', '/run/media/david/cf3f062d-1c9c-439d-aeb7-d0432f669e92', 1)
            self._db.addItemData(self._itemId, 'folderPaths', '/run/media/david/a707d25e-9ddf-46a4-a537-50f5dc49ac98', 2)
            self._db.addItemData(self._itemId, 'folderPaths', '/home/laptop', 3)
            self._db.addItemData(self._itemId, 'folderPaths', '/home/Pictures', 4)
            self._db.addItemData(self._itemId, 'folderPaths', '/home/david_1', 5)
            self._db.addItemData(self._itemId, 'folderPaths', '/run/media/david/3918fa86-d9e6-4355-8667-145b9856f0be/davidgc', 6)
            self._db.addItemData(self._itemId, 'folderPaths', '/run/media/david/media', 7)

            self._db.commit_db()

        else:
            itemURI = self._db.getItemURI(self._itemId)

        self._uri = itemURI

    def info(self):
        """ returns the objects information
        """
        return (self._title, self._version, self._descr)

    def getId(self):
        return self._engineId

    def setId(self, Id):
        self._engineId = Id

    def acceptDB(self, db):
        """ if this is declared the calling program will pass in the
        cursor from the exisiting db """
        self._db = db

    def config(self, config):
        """ pass in the configuration file
        """
        self._config = config

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions = {}

        #self._actions[''] = ('', ('')
        self._actions['getFiles'] = ('FileScanner', None)
        self._actions['getChecksum'] = ('checksum', ('uri'))

        return self._actions

    def run(self, *args, **kwargs):
        """ This acts as the marshalling function, this will call the relevant
        functions as defined in actions against the database...

        The sequence is...
            if ItemEvents are there then we process them, otherwise we call the generic
            getItemss function
        """
        self.actions()

        for funcName, action in self._actions.items():
            actionName, actionParams = action
            if actionParams == None:
                print 'Running %s.%s' % (self._title, funcName)
                func = getattr(self, funcName)
                func()
            else:
                self.runAction(actionName, funcName)
        self._db.commit_db()

    def runAction(self, actionName, funcName):
        """ will run the action specifiec in the action name
        """
        itemDataList = self._db.getItemList(self._engineId, actionName)
        actionId = self._db.addAction(actionName)
        func = getattr(self, funcName)
        print 'Running %s.%s' % (self._title, funcName)

        i = 0
        total = len(itemDataList)
        startTime = timeit.default_timer()

        for itemId, itemURI in itemDataList:
            i += 1
            func(itemURI)
            self._db.updateItem(self._engineId, itemId, actionId, datetime.datetime.now())

            if i % 1000 == 0:
                interTime = timeit.default_timer()
                step = ((interTime - startTime) / i)
                eta = step * (total - i)
                print 'Processing: %s / %s ETA: %ss at %s - %s' % (i, total, eta, step, itemURI)

                if self._db != None:
                    self._db.commit_db()

                runQueue = self._db.getConfig('RunQueue')
                if runQueue == 0:
                    break

            if self.useDelay == True:
                pTime = random.randint(1, 10)
                time.sleep(pTime)

        self._db.commit_db()

    def close(self):
        self._state = 'Dying'

    def getFiles(self):
        """ Will search the default paths...
        """
        fname = 'getFiles'

        self._state = 'Running...'

        # get the keywords to use
        folderPaths = self._db.getItemDataList(self._itemId, 'folderPaths')
        for uri in folderPaths:
            self.getItems(uri)

        self._state = 'Waiting...'

    def getChecksum(self, uri):
        """ Will search the path provided and apply the tags given
        """
        fname = 'getChecksum'
        self._state = 'Running...'

        #print '\t%s\t%s' % (fname, uri),
        # truncate the file://
        if uri[:5].lower() == 'file:':
            uri = uri[7:]

        md5Value = ''
        if not os.path.exists(uri):
            return '==missing=='
        try:
            md5 = hashlib.md5()
            with open(uri,'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                     md5.update(chunk)

            md5Value = md5.hexdigest()

            # now add this as itemData...
            itemId = self._db.addItem(self._engineId, uri, datetime.datetime.now())
            self._db.addItemData(itemId, 'MD5', md5Value, 0)
        except:
            print "\t\tUnexpected error in %s(-, %s):\t%s" % (fname, uri, sys.exc_info()[0])
            md5Value = '==error=='

        #print '\t%s' % md5Value
        self._state = 'Waiting...'

    def getItems(self, uri, actionId = -1):
        """ Will search the path provided and apply the tags given
        """
        fname = 'getItems'
        self._state = 'Running...'

        if actionId == -1:
            actionId = self._db.addAction('checksum')

        fileNames = []
        i = 0
        totalSize = 0L

        if not os.path.exists(uri):
            print '\tPath missing: %s' % uri
            return

        print '\t%s\t>> %s' % (fname, uri)

        items = dict()

        # first build a dict of files and thier metrics...
        for (pathStr, dirs, files) in os.walk(uri):
            # skip hidden http://stackoverflow.com/questions/13454164/os-walk-without-hidden-folders
            files = [f for f in files if not f[0] == '.']
            dirs[:] = [d for d in dirs if not d[0] == '.']

            head, tail = os.path.split(pathStr)
            #print '\t%s\t%s' % (fname, pathStr)

            fileDT = datetime.datetime.fromtimestamp(os.path.getmtime(pathStr))
            items.update({'folder://%s' % pathStr :(tail, fileDT, None, 'folder://%s' % pathStr)})

            for fileStr in files:
                try:
                    i += 1
                    item = os.path.join(pathStr,fileStr)
                    fileNames.append('file://%s' % item)

                    # get the file date...
                    fileDT = datetime.datetime.fromtimestamp(os.path.getmtime(item))
                    fileSize = os.path.getsize(item)
                    totalSize += fileSize

                    items.update({'file://%s' % item: (fileStr, fileDT, fileSize, 'folder://%s' % pathStr)})

                except:
                    print "\t\tUnexpected error in %s(-, %s):\t%s" % (fname, item, sys.exc_info()[0])

        #found = len(items)
        #print '\t%s\t%d\t%s' % (uri, found, totalSize)

        itemId_root = self._db.addItem(self._engineId, "folder://%s" % uri, fileDT)
        self._db.addItemLink(self._engineId, self._itemId, itemId_root, 'Contains')
        if self._db:
            self._db.commit_db()

        #print '\t{%s}\t[%s] %s' % (self._itemId, itemId_root, uri)

        # now to get the filetree
        items_db = dict()
        items_db = self._db.getItemTree(self._engineId, itemId_root)
        #print items_db

        #for key in items_db:
        #    print'\t%s' % (key)

        items_new = set(items) - set(items_db)
        items_old = set(items_db) - set(items)
        total = len(items_new)
        deleted = len(items_old)
        count = 0
        saves = 0
        print '\t[%s - %s (%s)]\t=\t%s' % (len(items), len(items_db), deleted, total)

        # add the new items
        folderName_old = 'folder://%s' % uri
        fileDT = datetime.datetime.fromtimestamp(os.path.getmtime(uri))
        itemId_folder = self._db.addItem(self._engineId, folderName_old, fileDT)

        head, tail = os.path.split(uri)
        folderName_parent = 'folder://%s' % head
        itemId_parent = self._db.addItem(self._engineId, folderName_parent, fileDT)
        #print '+++%s\t%s\t%s/%s' % (folderName_old, folderName_parent, itemId_folder, itemId_parent)

        # create a dictionary of folder names to store the itemId and parent id
        folders = dict()
        folders[folderName_parent] = (itemId_parent, 0)

        #print folders
        print '\t%s\t%s New : %s / %s' % (fname, uri, total, len(items))

        startTime = timeit.default_timer()

        for itemURI in items_new:
            fileName, fileDate, fileSize, folderName = items[itemURI]
            count += 1
            # we are in a new folder, so get the itemId and create link...
            if folderName != folderName_old:
                # check if the folder is present
                if folderName in folders:
                    itemId_folder, itemId_parent = folders[folderName]
                    saves += 1
                else:
                    itemId_folder = self._db.addItem(self._engineId, folderName, fileDate)
                    head, tail = os.path.split(pathStr)
                    folderName_parent = 'folder://%s' % head
                    itemId_parent = self._db.addItem(self._engineId, folderName_parent, fileDate)
                    #print '>>>%s\t%s\t%s/%s' % (folderName_parent, folderName, itemId_parent, itemId_folder)
                    folderName_old = folderName

                    if itemId_parent != itemId_folder:
                        self._db.addItemLink(self._engineId, itemId_parent, itemId_folder, 'Contains')

                    folders[folderName] = (itemId_folder, itemId_parent)

            itemId = self._db.addItem(self._engineId, itemURI, fileDate)

            if itemId_folder != itemId:
                self._db.addItemLink(self._engineId, itemId_folder, itemId, 'Contains')
                #print '[%s>>%s] %s %s %s %s' % (itemId_folder, itemId, fileName, fileDate, fileSize, folderName)

                # add the details
                self._db.addItemData(itemId, 'FileName', fileName, 0)
                self._db.addItemData(itemId, 'FileDate', fileDate, 0)
                self._db.addItemData(itemId, 'FileSize', fileSize, 0)

                # add a checksum event:
                self._db.addItemEvent(self._engineId, actionId, itemId)

            if (count % 1000) == 0:
                interTime = timeit.default_timer()
                step = ((interTime - startTime) / count)
                sec = datetime.timedelta(seconds=(step * (total - count)))
                d = datetime.datetime(1,1,1) + sec
                ets = "%d:%d:%d:%d" % (d.day-1, d.hour, d.minute, d.second)

                print 'Processing: %s / %s ETA: %s at %s >> %s - %s' % (count, total, ets, step, saves, itemURI )

                if self._db:
                    self._db.commit_db()

        if self._db:
            self._db.commit_db()

        self._state = 'Waiting...'
        return fileNames


def main():
    import imp
    import inspect
    import ConfigParser

    # the following is a hack to allow me to load mods and classes from a filepath
    corepath = '/home/david/Dropbox/StackingTurtles/projects/peregrin/poc'
    filepath = os.path.join(corepath, 'PeregrinDB.py')
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

    py_mod = imp.load_source(mod_name, filepath)
    classmembers = inspect.getmembers(py_mod, inspect.isclass)
    for cls in classmembers:
        my_class = getattr(py_mod, cls[0])
        if hasattr(my_class, 'connect_db'):
            db = cls[1]()
            break

    # configuration details
    cfg_path = os.path.join(corepath, 'PeregrinDaemon.cfg')
    config = ConfigParser.RawConfigParser()
    config.readfp(open(cfg_path))
    print config

    # database, details in the config file
    db.connect_db(config)

    # create the object
    obj = fileScanner()
    obj.acceptDB(db)
    obj._engineId = obj._db.addEngine(obj._title, obj._version, obj._descr)
    print obj._engineId

    obj.start()

    print obj.info()
    print obj.actions()

    obj.run()
    #obj.getItems('/home/david/Dropbox/haystack')

    del obj
    del db
    del config

    return 0

if __name__ == '__main__':
    main()

