#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  craigslist.py
#
#  Copyright 2013 David Gloyn-Cox <david@dreffed.com>
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
from BeautifulSoup import BeautifulSoup

import re
import mechanize
import cookielib
import timeit

import ConfigParser

import datetime
import os
import sys
import time
import random

class craigslist(object):
    """ this class will open the Craigslist net site, obtained via ItemData(<engine title>)
        it will then perform a series of keyword searches, keyword are obtained from the ItemId->itemData(keywords)
    """

    def __init__(self):
        print 'Init'
        self._title = 'CraigsList'
        self._version = '1.0'
        self._descr = 'CraigsList Search Processor.'
        self._engineId = -1
        self._state = 'Initialized'
        self._uri = ''
        self._db = None

    def state(self):
        """ Returns the state of the engine
        """
        return self._state

    def start(self):
        """ starts the engine, and will prepare any special function required
            This is the only method that Peregrin will need for it to work with this object.
            Will query the database for an entry in the ItemData table and return an URL
            from the ItemURL...
        """
        self._state = 'Started'
        self._itemId = self._db.getItemData(self._title)
        if self._itemId <= 0:
            # missing value need to add it in...
            itemURI = 'craigslist.ca'

            self._itemId = self._db.addItem(self._engineId, itemURI, datetime.datetime.now())
            self._db.addItemData(self._itemId, self._title, itemURI, 0)

            # also set up the default keywords...
            # breakdown is  uriPrefix|urlLang|urlCountry|path|query|catAbj
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|business+intelligence|jjj', 0)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|database|jjj', 1)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|project+management|jjj', 2)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|software+engineer|jjj', 3)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|strategic|jjj', 4)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|business+analysis|jjj', 5)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|quality+analysis|jjj', 6)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|quality+assurance|jjj', 7)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|erp+implementation|jjj', 8)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|software+selection|jjj', 9)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|system+integration|jjj', 10)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|User+experience+UX|jjj', 11)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|dev+ops+data+dataops+devops|jjj', 12)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|fun+energetic|jjj', 13)
            self._db.addItemData(self._itemId, 'keyword', 'vancouver|en|ca|/search/|project+coordination|jjj', 14)
            
    
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

    def acceptDB(self, db):
        """ if this is declared the calling program will pass in the
        cursor from the existing db """
        self._db = db

    def config(self, config):
        """ pass in the configuration file
        """
        self._config = config

    def run(self, *args, **kwargs):
        self.actions()

        for funcName, action in self._actions.items():
            actionName, actionParams = action
            if actionParams == None:
                func = getattr(self, funcName)
                print '\tRunning %s.%s()' % (self._title, funcName)
                func()
            else:
                self.runAction(actionName, funcName)
        self._db.commit_db()

    def runAction(self, actionName, funcName):
        """ will run the action specific in the action name
        """
        itemDataList = self._db.getItemList(self._engineId, actionName)
        actionId = self._db.addAction(actionName)
        func = getattr(self, funcName)
        i = 0
        total = len(itemDataList)
        startTime = timeit.default_timer()
        print '\tRunning %s.%s() {%s} -> %s [%s] {%s}' % (self._title, funcName, actionName, total, startTime, actionId)

        for itemId, itemURI in itemDataList:
            i += 1
            func(itemURI)
            self._db.updateItem(self._engineId, itemId, actionId, datetime.datetime.now())

            if i % 1000 == 0:
                interTime = timeit.default_timer()
                step = ((interTime - startTime) / i)
                eta = step * (total - i)
                print '\t\tProcessing [%s]: %s / %s ETA: %ss at %s' % (self._title, i, total, eta, step)

                if self._db != None:
                    self._db.commit_db()

                runQueue = self._db.getConfig('RunQueue')
                if runQueue == 0:
                    break

            pTime = random.randint(1, 10)
            time.sleep(pTime)

        self._db.commit_db()

    def close(self):
        self._state = 'Dying'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions = {}
        self._actions['getItems'] = ('search', None)
        self._actions['getJobs'] = ('extractor', ('url'))

        return self._actions

    def getItems(self):
        """ takes the provided URI and will
        """
        print '\tFetching : %s\t%s [%s]' % (self._title, self._uri, self._itemId)

        # get the keywords to use
        if self._db != None:
            keywords = self._db.getItemDataList(self._itemId, 'keyword')

        # for each key word get the links
        for keyword in keywords:
            #print '\tRetrieve:\t%s' % keyword
            itemId = self.process_tocpage(self._uri, keyword)

            # now add the link...
            # addItemLink(self, engineId, itemIdLeft, itemIdRight, linkType)
            self._db.addItemLink(self._engineId, self._itemId, itemId, 'search')

            pTime = random.randint(1, 10)
            time.sleep(pTime)

        if self._db != None:
            self._db.commit_db()

    def getJobs(self, itemURI):
        """ Will process the provided URI and will extract the relevant job details
            and save into the itemData table.
        """
        """ This will take the search result and for each item will pull off the details,
            for ease the system should only search new / changed items.
            For Job Searches:
                From each URL get the following
                    Job Description
                    Job Posted Date
                    Job Company
        """
        fname = 'getJobs'
        itemId = -1
        try:
            itemId = self._db.addItem(self._engineId, itemURI, datetime.datetime.now())
            #print '\t%s\t[%s] %s' % (fname, itemId, itemURI)

            br = self.open_page(itemURI)
            html = br.response().read()
            pool = BeautifulSoup(html)

#==============================================================================
#             #now process the returned page...
#             Job Description
#                 <section id="postingbody"> = job description </section>
#
#             Date and other info
#                 <div class="postinginfos">
#                     <p class="postinginfo">Posting ID: 3914018776</p>
#                         <p class="postinginfo">Posted:
#                             <date title="1372966900000">2013-07-04, 12:41PM PDT</date>
#                         </p>
#                     <p class="postinginfo">
#                         <a class="tsb" href="https://accounts.craigslist.org/eaf?postingID=3914018776&amp;token=U2FsdGVkX181NDAxNTQwMXQ5pjyGG99xZ39canpZlBvlXu1VN2Ect5v3Q7zVZPfvLCHAJKfD4J2NXVUWXLcf35vJtoJnXBbSetEZdB00sZo">email to a friend</a>
#                     </p>
#                </div>
#==============================================================================
            sections = pool.findAll('section', {'id' : 'postingbody'})
            i = 0
            for section in sections:
                jobDesc = section.text
                self._db.addItemData(itemId, 'JobDescription', jobDesc, i)
                i += 1

        except:
            print "\t\tUnexpected error in %s(-, %s, %s):\t%s" % (fname, itemId, itemURI, sys.exc_info()[0])

    # these are generally internals for the class, called by the above methods
    def open_page(self, url):
        """ Will take the passed url and open a browser instance, this will
            be returned to the calling code.
            This model uses mechanize, though it could be changed to another
            by changing this code.
        """
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
        br.open(url)

        return br

    def process_tocpage(self, uri, keyword):
        """
        """
        fname = 'get_page'
        itemId = -1

        # split out the keyword
        # breakdown is  uriPrefix|urlLang|urlCountry|path|query|catAbj
        try:
            uriPrefix, urlLang, urlCountry, path, query, catAbj = keyword.split('|')
            baseURI = 'http://%s.%s.%s.%s' % (uriPrefix, urlLang, uri, urlCountry)
            itemURI = '%s%s%s?zoomToPosting=&query=%s&srchType=A' % (baseURI, path, catAbj, query) # catAbb=%s&

            itemId = self._db.addItem(self._engineId, itemURI, datetime.datetime.now())
            self._db.addItemData(itemId, 'keyword', keyword, 0)

            print '\t\t[%s] %s' % (itemId, itemURI)
            br = self.open_page(itemURI)

#==============================================================================
#             <p class="row" data-pid="3924331229">
#                 <a href="/van/sof/3924331229.html" class="i"></a>
#                 <span class="pl"> <span class="star"></span>
#                     <small> <span class="date">Jul  9</span></small>
#                     <a href="/van/sof/3924331229.html">Intermediate to Senior Oracle DBA</a>
#                 </span>
#                 <span class="l2">
#                     <span class="pnr">
#                         <span class="pp"></span>
#                         <span class="px">
#                             <span class="p"> </span>
#                         </span>
#                     </span>
#                     <a class="gc" href="/sof/" data-cat="sof">software/QA/DBA/etc</a>
#                 </span>
#            </p>
#==============================================================================
            all_links = [l for l in br.links(url_regex='.*\/\d+\.html$')]
            reFind = re.compile('.*\/(\d.+)\.html')
            for link in all_links:
                if link.text != '':
                    if link.url[:4] == 'http':
                        jobURI = link.url
                    else:
                        jobURI = '%s%s' % (baseURI, link.url)
                    jobTitle = link.text

                    #print '\t%s\t%s\t%s' % (link.url, jobTitle, jobURI)

                    result = reFind.match(link.url)
                    if result:
                        jobId = result.group(1)
                    else:
                        jobId = '-1'

                    self.addListing(jobId, jobTitle, jobURI, itemId)

        except:
            print "\t\tUnexpected error in %s(-, %s, %s):\t%s" % (fname, uri, keyword, sys.exc_info()[0])

        return itemId

    def addListing(self, jobId, jobTitle, jobURI, itemId_parent = None):
        """ Will add the listing to the database,
            self._itemId -> items
                listing -> itemId
                    itemId -> itemLinks
        """
        #print '\t\t\t[%s] %s \n\t\t\t\t>>%s' % (jobId, jobTitle, jobURI),

        # add the item
        itemId = self._db.addNewItem(self._engineId, jobURI, datetime.datetime.now(), ('extractor', 'ml'))
        if itemId > 0:
            print '\t[%s]\t%s (%s)' % (itemId, jobTitle, jobId)
            # add in the item data...
            self._db.addItemLink(self._engineId, self._itemId, itemId, 'contains')

            # add in the link
            self._db.addItemData(itemId, 'JobId', jobId, 0)
            self._db.addItemData(itemId, 'JobTitle', jobTitle, 0)

            if itemId_parent > 0:
                self._db.addItemLink(self._engineId, itemId_parent, itemId, 'contains')

            return True
        else:
            return False


def main():
    import imp
    import inspect

    # the following is a hack to allow me to load mods and classes from a filepath
    #corepath = '/home/davidg/Dropbox/StackingTurtles/projects/peregrin/poc'
    modPath = os.path.dirname(__file__)
    corepath = os.path.split(modPath)[0]
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
    print 'Running >> %s' % datetime.datetime.today()

    # database, details in the config file
    db.connect_db(config)

    # create the object
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)

    # open the first class found...    
    obj = craigslist() #classes[0][1]()
    obj.acceptDB(db)

    obj._engineId = obj._db.addEngine(obj._title, obj._version, obj._descr)
    obj._db.commit_db()

    obj.start()

    print 'ItemId:\t%s\t[%s]' % (obj._itemId, obj._engineId)

    print obj.info()
    print obj.actions()

    obj.run()

    del obj
    del db
    del config
    
    print 'Ending >> %s' % datetime.datetime.today()
    print '================================================'
    
    return 0

if __name__ == '__main__':
    main()

