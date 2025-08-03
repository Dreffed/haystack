# -*- coding: utf-8 -*-
"""
Created on Fri Mar 28 10:12:26 2014

@author: david gloyn-cox
"""
from bs4 import BeautifulSoup
import configparser
import http.cookiejar as cookielib
import datetime
import mechanize
import os
import re
import sys
import timeit

class webScraper(object):
    def __init__(self):
        print('Init')
        super(webScraper, self).__init__()
        self._title = self.__class__.__name__
        self._version = '1.0'
        self._descr = '''
A web scraper that will do a simple scrape of web elements:
    Elements:
        Links
            will track the depth it is found at, this depth will limit the amount of recursion the site can go too, to handle spider traps
        Images
            download basic info about the image
                size
                url
                alt text
        Forms
            formname
                Fields
                    Name
                    Value
                    Default
                    Type
        
    '''
        self._engineId = -1
        self._state = 'Initialized'
        self._db = None
    
        # set this to true if this class is to handle any raised action, not just it own raised actions
        self._actionSearch = False
        
        # add any class specific fields below
        #self._downloadPath = ''
        #self._youtube = ''

    def state(self):
        """ Returns the state of the engine
        """
        return self._state

    def start(self):
        """ starts the engine, and will prepare any special function retquired
            This is the only method that Peregrin will need for it to work with this object.
        """
        self._state = 'Started'
        self._itemId = self._db.getItemData(self._title)
        if self._itemId <= 0:
            # missing value need to add it in...
            itemURI = self.__class__.__name__

            self._itemId = self._db.addItem(self._engineId, itemURI, datetime.datetime.now())
            self._db.addItemData(self._itemId, self._title, itemURI, 0)

            # also set up the default keywords...
            self._db.addItemData(self._itemId, 'keyword', 'a', 0)
            self._db.addItemData(self._itemId, 'keyword', 'form', 0)
            self._db.addItemData(self._itemId, 'keyword', 'img', 0)

            if self._db != None:
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

    def config(self, config):
        """ pass in the configuration file
        """
        self._config = config
        
        # read in the class variables if needed here
        self._recursiondepth = self._config.get('Depths', 'webScraper')

    def acceptDB(self, db):
        """ if this is declared the calling program will pass in the
        cursor from the exisiting db """
        self._db = db

    def run(self, *args, **kwargs):
        self.actions()

        for funcName, action in self._actions.items():
            actionName, actionParams = action
            if actionParams == None:
                func = getattr(self, funcName)
                func()
            else:
                self.runAction(actionName, funcName)
                
        self._db.commit_db()

    def runAction(self, actionName, funcName):
        """ will run the action specifiec in the action name
        """   
        actionId = self._db.addAction(actionName)
        func = getattr(self, funcName)

        # get the Iems based on an actionId only, TRUE causes this functonality
        itemDataList = self._db.getItemList(self._engineId, actionName, self._actionSearch)

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
                print('Processing: %s / %s ETA: %ss at %s' % (i, total, eta, step))

                if self._db != None:
                    self._db.commit_db()

        self._db.commit_db()

    def close(self):
        self._state = 'Dying'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions = {}

        # this is the list that registeres this class for certain actions
        # The dictionary is by function name (must be defined in this class)
        # then the actionName, used to get the actionID, and the parameters required
        self._actions['walkSite'] = ('watch',('uri'))
        #self._actions[''] = ('',(''))

        return self._actions

    def walkSite(self, uri):
        """ will walk and harvest links...
        """
        
        return self.getDocuments(uri)


    # these are generally internals for the class, called by the above methods
    # generic method used to return a mechanised version of the page...
    # can be removed if not needed...
    def open_page(self, uri):
        """ Will take the passed uri and open a browser instance, this will
            be returned to the calling code.
            This model uses mechanize, though it could be changed to another
            by changing this code.
        """
        fname = 'open_page'
        br = None

        try:
            _dicProps = {}
            _dicProps["equiv"] = True
            _dicProps["gzip"] = True
            _dicProps["redirect"] = True
            _dicProps["referer"] = True
            _dicProps["robots"] = False

            _dicProps["headers"] = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]

            # empty browser
            br = mechanize.Browser()

            # Cookie Jar
            cj = cookielib.LWPCookieJar()
            br.set_cookiejar(cj)

            # Browser options
            br.set_handle_equiv(_dicProps["equiv"])
            br.set_handle_gzip(_dicProps["gzip"])
            br.set_handle_redirect(_dicProps["redirect"])
            br.set_handle_referer(_dicProps["referer"])
            br.set_handle_robots(_dicProps["robots"])

            # Follows refresh 0 but not hangs on refresh > 0
            br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

            # User-Agent (this is cheating, ok?)
            br.addheaders = _dicProps["headers"]

            # The site we will navigate into, handling it's session
            print('\t%s\t%s' % (fname,uri))
            br.open(uri)
        except:
            print("\t\tUnexpected error in %s(-, %s):\t%s" % (fname, uri, sys.exc_info()[0]))

        return br


def main():
    import importlib.util
    import inspect

    # the following is a hack to allow me to load mods and classes from a filepath
    #corepath =  #'/home/davidg/Dropbox/StackingTurtles/projects/peregrin/poc'
    modPath = os.path.dirname(__file__)
    corepath = os.path.split(modPath)[0]
    filepath = os.path.join(corepath, 'PeregrinDB.py')
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])
    
    try:
        spec = importlib.util.spec_from_file_location(mod_name, filepath)
        py_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_mod)
        classmembers = inspect.getmembers(py_mod, inspect.isclass)
        for cls in classmembers:
            my_class = getattr(py_mod, cls[0])
            if hasattr(my_class, 'connect_db'):
                db = cls[1]()
                break
    
        # configuration details
        cfg_path = os.path.join(corepath, 'PeregrinDaemon.cfg')
        config = configparser.RawConfigParser()
        with open(cfg_path) as f:
            config.read_file(f)
        print('Running >> %s' % datetime.datetime.today())
    
        # database, details in the config file
        db.connect_db(config)
    except:
        # handle this if the db is needed....
        pass
        
    # create the object
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for childClass in classes:
        print(childClass[0])

    # open the first class found...    
    obj = classes[0][1]()
    obj.config(config)
    obj.acceptDB(db)

    obj._engineId = obj._db.addEngine(obj._title, obj._version, obj._descr)
    obj._db.commit_db()

    obj.start()

    print('EngineId:\t%s\t[%s]' % (obj._itemId, obj._engineId))

    print(obj.info())
    print(obj.actions())

    obj.run()

    del obj
    del db
    del config
    
    print('Ending >> %s' % datetime.datetime.today())
    print('================================================')
    
    return 0

if __name__ == '__main__':
    main()

      