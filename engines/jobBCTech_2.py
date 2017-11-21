#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  bcTechJob.py
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
from bs4 import BeautifulSoup
from urllib.parse import urlparse

import timeit
import mechanicalsoup
from http import cookiejar

import datetime
import os
import sys
import time
import random

class bcTechJob(object):
    """ this class will open the BC Tech net site, obtained via ItemData(<engine title>)
        it will then perform a series of keyword searches, keyword are obtained from the ItemId->itemData(keywords)
    """

    def __init__(self):
        print('Init')
        self._title = 'BC Technet'
        self._version = '2.0'
        self._descr = 'Job Search Processor for the BC Technology web site.'
        self._engine_id = -1
        self._state = 'Initialized'
        self._uri = ''
        self._items = 0
        self._db = None

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
            itemURI = 'http://www.bctechnology.com/scripts/search_form.cfm'
            self._itemId = self._db.addItem(self._engine_id, itemURI, datetime.datetime.now())
            self._db.addItemData(self._itemId, self._title, itemURI, 0)

            # also set up the default keywords...
            self._db.addItemData(self._itemId, 'keyword', 'business intelligence', 0)
            self._db.addItemData(self._itemId, 'keyword', 'database', 1)
            self._db.addItemData(self._itemId, 'keyword', 'project management', 2)
            self._db.addItemData(self._itemId, 'keyword', 'software engineer', 3)
            self._db.addItemData(self._itemId, 'keyword', 'strategic', 4)
            self._db.addItemData(self._itemId, 'keyword', 'business analysis', 5)
            self._db.addItemData(self._itemId, 'keyword', 'software selection', 6)
            self._db.addItemData(self._itemId, 'keyword', 'erp implementation', 7)
            self._db.addItemData(self._itemId, 'keyword', 'system integration', 8)
            self._db.addItemData(self._itemId, 'keyword', 'quality assurance', 9)
            self._db.addItemData(self._itemId, 'keyword', 'User experience UX', 11)
            self._db.addItemData(self._itemId, 'keyword', 'data dataops', 10)
            self._db.addItemData(self._itemId, 'keyword', 'dev ops devops', 12)
            self._db.addItemData(self._itemId, 'keyword', 'fun energetic', 13)
            self._db.addItemData(self._itemId, 'keyword', 'project coordination', 14)
            
            self._db.commit_db()

        else:            
            itemURI = self._db.getItemURI(self._itemId)

        self._uri = itemURI

    def info(self):
        """ returns the objects information
        """
        return (self._title, self._version, self._descr)

    def getId(self):
        return self._engine_id

    def setId(self, Id):
        self._engine_id = Id

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
        self._actions['getItems'] = ('search', None)
        self._actions['getJobs'] = ('extractor', ('url'))

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
                print('Running %s.%s' % (self._title, funcName))
                func = getattr(self, funcName)
                func()
            else:
                self.runAction(actionName, funcName)
        self._db.commit_db()

    def runAction(self, actionName, funcName):
        """ will run the action specifiec in the action name
        """
        itemDataList = self._db.getItemList(self._engine_id, actionName)
        actionId = self._db.addAction(actionName)
        func = getattr(self, funcName)
        print('Running %s.%s' % (self._title, funcName))

        i = 0
        total = len(itemDataList)
        startTime = timeit.default_timer()

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

                runQueue = self._db.getConfig('RunQueue')
                if runQueue == 0:
                    break

            pTime = random.randint(1, 10)
            time.sleep(pTime)

        self._db.commit_db()

    def close(self):
        self._state = 'Dying'

    def getItems(self):
        """ takes the provided URI and will
        """
        # check to see if any jobs need to be processed first...
        print('\tFetching : %s\t%s' % (self._title, self._uri))
        self._state = 'Running...'

        # get the keywords to use
        keywords = self._db.getItemDataList(self._itemId, 'keyword')

        # for each key word get the links
        for keyword in keywords:
            print('\tRetrieve:\t%s' % keyword)
            self.get_page(self._uri, keyword)

        self._db.commit_db()

        items = self._db.getItemList(self._engine_id, 'extractor')
        self._items = len(items)
        self._state == 'Waiting...'

    def getJobs(self, uri):
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
        stage = 0
        fname = 'getJobs'
        try:
            self._state = 'Running...'                
            stage +=1
            itemId = self._db.addItem(self._engine_id, uri, datetime.datetime.now())
            
            #print('\t%s\t[%s] %s' % (fname, itemId, uri))
            br = self.open_page(uri)
                
            stage +=1

            # job fields:
            br.select_form(name="frm1")
            stage +=1

            #jobTitle = br.form['position']
            jobDate = br.form['insert_date']
            companyName = br.form['company_name']
            companyId = br.form['company_id']
            jobTitle = br.form['position']
            jobID = br.form['id']
            stage +=1
            
            #print('\t%s {%s}\t%s [%s]' % (jobTitle, jobDate, companyName, companyId))
            self._db.addItemData(itemId, 'CompanyId', companyId, 0)
            self._db.addItemData(itemId, 'CompanyName', companyName, 0)
            self._db.addItemData(itemId, 'JobDate', jobDate, 0)
            self._db.addItemData(itemId, 'JobTitle', jobTitle, 0)
            self._db.addItemData(itemId, 'JobID', jobID, 0)
            stage +=1

            #print('\tJob Desc',)
            # now we need the description and requirements...
            html = br.response().read()
            pool = BeautifulSoup(html)
            stage +=1

            # select tables under class gold
            # look at first row, it should have a image tag of Job Description
            groupTables = pool.findAll('table', {'class' : 'gold'})
            stage +=1

            jobDesc = ''
            for table in groupTables:
                row = table.findAll('tr', limit=1)
                img = row[0].findAll('img', limit=1)
                for attr, value in img[0].attrs:
                    if attr == 'alt' and value == 'Job Description':
                        jobDesc = ''.join(table.findAll(text=True))

            #print(jobDesc)
            stage +=1
            self._db.addItemData(itemId, 'JobDescription', str(jobDesc), 0)
            stage +=1

        except:
            print("\t\tUnexpected error in %s->%s (%s, %s):\t%s" % (fname, stage, itemId, uri, sys.exc_info()[0]))

        self._state == 'Waiting...'

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

        _dicProps["headers"] = [('User-agent', )]

        # empty browser
        br = mechanicalsoup.StatefulBrowser(
            soup_config={'features': 'lxml'},
            raise_on_404=True,
            user_agent='Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1',
        )

        # The site we will navigate into, handling it's session
        br.open(url)

        return br

    def get_page(self, uri, keyword):
        """
        """
        fname = 'get_page'
        br = self.open_page(uri)

        # Select the first (index zero) form
        search_form = br.select_form('form[name="frm1"]')  
        print(search_form)

        # submit the fields...
        br['keyword'] = keyword

        resp = br.submit_selected()
        print(br.get_current_page().url)

        baseParse = urlparse(resp.url)
        baseurl = "%s://%s" % (baseParse.scheme, baseParse.netloc)

        # loop until all jobs found
        hasMore = True
        count = 0
        jobId = 0
        stage = 0

        while hasMore:
            count += 1

            # gets the next page
            next_links = []
            all_links = []
            links  = [l for l in br.get_current_page().select('a')]
            for l in links:
                if l.text.startswith('Next'):
                    next_links.append(l)
                    break

                if l.id == 'job-title-link':
                    all_links.append(l)
                
            print(all_links)
            print(next_links)
            return

            # process these links...
            found = len(all_links)
            
            new = 0
            for link in all_links:
                try:
                    stage = 1
                    # extract the job id and other info...
                    urlDets = urlparse(link.url)
                    
                    params = dict([part.split('=') for part in urlDets.query.split('&')])
                    jobId = params['showid']

                    stage += 1
                    jobTitle = link.text

                    for attr, value in link.attrs:
                        if attr == 'title':
                            jobTitle = value

                    # we have job id... check if it exists...
                    stage += 1

                    jobURI = baseurl + link.url #'%s/scripts/show_job.cfm?id=%s' % (baseurl, jobId)
                    if self.addListing(jobId, jobTitle, jobURI):
                        print('\t\t\t[%s] %s' % (jobId, jobTitle))
                        new += 1

                    stage += 1

                except NameError as e:
                    print("\t\tError in %s(Loop:%s, Stage:%s, Job:%s)\t%s:" % (fname, count, stage, jobId, e.args[0]))

                except:
                    print("\t\tUnexpected error in %s(Loop:%s, Stage:%s, Job:%s):\t%s" % (fname, count, stage, jobId, sys.exc_info()[0]))

            # go to the next page
            print('\t\t>> %s/%s ' % (new, found))

            if len(nextLink) > 0:
                br.follow_link(nextLink[0])
                results_page = br.get_current_page()
                hasMore = (new > 0)

                pTime = random.randint(1, 10)
                time.sleep(pTime)

            else:
                hasMore = False

    def addListing(self, jobId, jobTitle, jobURI):
        """ Will add the listing to the database,
            self._itemId -> items
                listing -> itemId
                    itemId -> itemLinks
        """
        #print('\t\t\t[%s] %s \n\t\t\t\t>>%s' % (jobId, jobTitle, jobURI))

        # add the item
        itemId = self._db.addNewItem(self._engine_id, jobURI, datetime.datetime.now(), ('extractor', 'ml'))
        if itemId > 0:
            # add in the item data...
            self._db.addItemLink(self._engine_id, self._itemId, itemId, 'contains')

            # add in the link
            self._db.addItemData(itemId, 'JobId', jobId, 0)
            self._db.addItemData(itemId, 'JobTitle', jobTitle, 0)

            return True
        else:
            return False


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

    # configuration details
    cfg_path = os.path.join(corepath, 'config', 'PeregrinDaemon.cfg')
    config = configparser.RawConfigParser()
    config.readfp(open(cfg_path))
    print('Running >> %s' % datetime.datetime.today())

    # database, details in the config file
    db.connect_db(config)

    # create the object
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)
    for clsObj in classes:
        print('\t%s [%s]\t%s' % (clsObj[1].__name__, clsObj[1].__module__, __name__))
        if clsObj[1].__module__ == __name__:
            obj = clsObj[1]()
            print('\t%s [%s]' % (obj.__class__.__name__, obj.__module__))
    
    #obj = bcTechJob()       
    if obj:
        # open the first class found...    
        #obj = bcTechJob() #classes[0][1]()
        obj.acceptDB(db)
    
        obj._engine_id = obj._db.addEngine(obj._title, obj._version, obj._descr)
        obj._db.commit_db()
    
        obj.start()
    
        print('ItemId:\t%s\t[%s]' % (obj._itemId, obj._engine_id))
    
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

