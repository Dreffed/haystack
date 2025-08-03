#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  fileDownloader.py
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
import datetime
import timeit

import urllib.request
import shutil
from urllib.parse import urlparse
import os
import sys

from subprocess import Popen, PIPE

import mechanize
import http.cookiejar as cookielib

class fileDownloader(object):

    def __init__(self):
        print('Init')
        self._title = 'FileDownloader'
        self._version = '1.0'
        self._descr = '''Will download all link in the referenced page based on the type requested.'''
        self._engine_id = -1
        self._state = 'Initialized'
        self._downloadPath = ''
        self._youtube = ''
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
        self._itemId = self._db.getItemData(self._title)
        if self._itemId <= 0:
            # missing value need to add it in...
            itemURI = 'fileDownloader.py'

            self._itemId = self._db.addItem(self._engine_id, itemURI, datetime.datetime.now())
            self._db.addItemData(self._itemId, self._title, itemURI, 0)

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
        return self._engine_id

    def setId(self, Id):
        self._engine_id = Id

    def config(self, config):
        """ pass in the configuration file
        """
        self._config = config
        self._downloadPath = self._config.get('Paths', 'downloads')
        self._youtube = self._config.get('Paths', 'youtube')

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
        itemDataList = self._db.getItemList(self._engine_id, actionName, True)

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

        self._db.commit_db()


    def close(self):
        self._state = 'Dying'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.
        """
        self._actions = {}
        self._actions['getAll'] = ('download',('uri'))

        self._actions['getDocuments'] = ('dl-books',('uri'))
        self._actions['getMedia'] = ('dl-media',('uri'))
        self._actions['getApplications'] = ('sl-app',('uri'))
        self._actions['getArchives'] = ('dl-arc',('uri'))
        self._actions['getYoutube'] = ('dl-youtube',('uri'))

        return self._actions

    def    getAll(self, uri):
        """ Will query the page and download PDF Files...
        """
        return self.getDocuments(uri)

    def    getYoutube(self, uri):
        """ Will query the page and download PDF Files...
        """
        try:
            outputPath = '-o' + self._youtube.strip() + '/%(title)s.%(ext)s'

            p = Popen(['youtube-dl', uri, outputPath, '--keep-video','--restrict-filenames', '--write-info-json', '--add-metadata'],stdout=PIPE)
            stdout, stderr = p.communicate()
            print('\t%s - %s' % (uri, outputPath))
            
        except:
            print('ERROR')
            print(stderr)

    def    getDocuments(self, uri):
        """ Will query the page and download PDF Files...
        """
        reg_str = r'^.*[.](?P<ext>pdf|chm|doc|docx|txt|ppt|ps)$'
        return self.get_links(reg_str, uri, self._downloadPath)

    def    getMedia(self, uri):
        """ Will query the page and download CHM Files...
        """
        reg_str = r'^.*[.](?P<ext>mp.|mpeg|avi|swf|jpg|jpeg|png)$'
        return self.get_links(reg_str, uri, self._downloadPath)

    def    getApplications(self, uri):
        """ Will query the page and download PDF Files...
        """
        reg_str = r'^.*[.](?P<ext>exe|cab)$'
        return self.get_links(reg_str, uri, self._downloadPath)

    def    getArchives(self, uri):
        """ Will query the page and download PDF Files...
        """
        reg_str = r'^.*[.](?P<ext>zip|rar|tar\.gz|tgz|7z)$'
        return self.get_links(reg_str, uri, self._downloadPath)

    # these are generally internals for the class, called by the above methods
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

    def get_links(self, reg_str, uri, download_path):
        """ Will open the page in the uri and search for links to that statisfy the reg_str,
            once found it will download the file.
        """
        fname = 'get_links'

        br = self.open_page(uri)

        urlDets = urlparse(uri)

        fileNames = []
        try:
            all_links = [l for l in br.links(url_regex=reg_str)]
        except:
            all_links = []

        for link in all_links:
            try:
                itemId = -1

                # extract other info...
                if link.base_url == '':
                    dUrl = uri + link.uri
                else:
                    dUrl = link.base_url + link.url

                if self._db != None:
                    itemId = self._db.addNewItem(self._engine_id, dUrl, datetime.datetime.now())

                if itemId > 0:
                    fileName = self.download(dUrl, download_path)

                    if self._db != None:
                        itemIdFile = self._db.addItem(self._engine_id, fileName, datetime.datetime.now(), ('checksum',))
                        self._db.addItemLink(self._engine_id, itemId, itemIdFile, "download")

                    fileNames.append(fileName)

            except NameError as e:
                print("\t\tError\t%s:" % e.args[0])

            except:
                print("\t\tUnexpected error:\t%s" % sys.exc_info()[0])

        self._state = 'Waiting...'

        return True

    def getFileName(self, uri,openUrl):
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info()['Content-Disposition'].split(';')))
            if 'filename' in cd:
                filename = cd['filename'].strip("\"'")
                if filename: return filename
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse(openUrl.uri).path)

    def download(self, uri, download_path):
        fname = 'download'
        print(fname, uri, download_path)

        req = urllib.request.Request(uri)
        r = urllib.request.urlopen(req)
        urlDets = urlparse(uri)
        fileName = ''

        try:
            fileName = os.path.join(download_path, urlDets.netloc, urlDets.path.strip("/"))
            dirName = os.path.dirname(fileName)

            if not os.path.exists(dirName):
                os.makedirs(dirName)

            infoName = fileName + '.uri'

            with open(infoName, 'wb') as infoF:
                infoF.write('[InternetShortcut]\nURL=%s\nDATE=%s' % (uri,datetime.datetime.now()))

            with open(fileName, 'wb') as f:
                shutil.copyfileobj(r,f)

        finally:
            r.close()

        return fileName

def main():
    import importlib.util
    import inspect
    import configparser

    # the following is a hack to allow me to load mods and classes from a filepath
    modPath = os.path.dirname(__file__)
    corepath = os.path.split(modPath)[0]
    filepath = os.path.join(corepath, 'db', 'PeregrinDB.py')
    mod_name,file_ext = os.path.splitext(os.path.split(filepath)[-1])

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
    cfg_path = os.path.join(corepath, 'config', 'PeregrinDaemon.cfg')
    config = configparser.RawConfigParser()
    with open(cfg_path) as f:
        config.read_file(f)
    print('Running >> %s' % datetime.datetime.today())

    # database, details in the config file
    db.connect_db(config)

    # create the object
    # create the object
    classes = inspect.getmembers(sys.modules[__name__], inspect.isclass)

    # open the first class found...    
    obj = fileDownloader() #classes[0][1]()
    obj.config(config)
    obj.acceptDB(db)

    obj._engine_id = obj._db.addEngine(obj._title, obj._version, obj._descr)
    obj._db.commit_db()

    obj.start()

    print('EngineId:\t%s\t[%s]' % (obj._itemId, obj._engine_id))

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

