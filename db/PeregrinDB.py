#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  PeregrinDB.py
#
#  Copyright 2013 David Gloyn-Cox <david@leviathan>
#
import sys
import pymysql as mdb
import datetime

class PeregrinDB:
    """ load up the database, and the engines, then check for events in the queue
        if any detected then fire the engines as appropriate.
    """

    def __init__(self):
        """ initializes the class
        """
        self._con = None
        self._cursor = None

        self._title = 'PeregrinDB'
        self._version = '1.0'
        self._descr = 'Peregrin Database Engine'
        self._engine_id = -1

    def __del__(self):
        """ removes the connect to the database if connected
        """
        if self._con:
            self._con.close()

    def info(self):
        """ returns the objects information
        """
        return (self._title, self._version, self._descr)

    def connect_db(self, config):
        """ Connect to the database, reads from the pass ed
        configuration
        """
        fname = "_connection_db"
        try:
            server_name = config.get('Database', 'Server')
            user_name = config.get('Database', 'User')
            password=config.get('Database', 'Password')
            db_name=config.get('Database', 'Schema')
            
            self._con = mdb.connect(host=server_name,user=user_name,password=password,db=db_name,charset='utf8mb4',cursorclass=mdb.cursors.DictCursor)

            self._cursor = self._con.cursor()
            self._engine_id = self.addEngine(self._title, self._version, self._descr)            
            self._con.commit()

        except mdb.Error as e:
            print("Error %d: %s" % (e.args[0],e.args[1]))
            raise

        except:
            print("\tUnexpected error in %s:\t%s" % (fname, sys.exc_info()[0]))
            raise

    def commit_db(self):
        """ Calls commit on the database 
        """
        if self._con:
            self._con.commit()

    def close_db(self):
        """ closes the connectioon to the db and
        sets the obj to None
        """
        if self._con:
            self._con.close()
            self._con = None

    def addStatus(self, engineId, actionId, message):
        """ This will add a status message into the system and commit it, allow the
            other applications to peek into the other process statuses
        """
        fName = 'addStatus'
        try:
            self._cursor.execute("INSERT INTO Status (engineId, actionId, StatusMessage, StatusDate) VALUES (%s, %s , %s, %s);",(engineId, actionId, message, datetime.datetime.now()))

            self._con.commit()

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionId, message, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionId, message, sys.exc_info()[0]))

    def getStatus(self):
        """ Returns the last 1000 status messages
        """
        fName = 'getStatus'
        status = []

        #print('%s>>' % (fName),)
        try:
            self._cursor.execute("SELECT statusId, EngineId, ActionId, StatusMessage, StatusDate FROM Status LIMIT 1000;")
            rows = self._cursor.fetchall()
            #print('\t%s' % len(rows))
            for row in rows:
                status.append(row)

        except mdb.Error as e:
            print("\tError in %s(-):\t%s" % (fName, e))

        except Exception as e:
            print("\tUnexpected error in %s(-):\t%s" % (fName, e))

        finally:
            return status

    def addConfig(self, engineId, configName, configValue):
        """ This will add a status message into the system and commit it, allow the
            other applications to peek into the other process statuses
        """
        fName = 'addConfig'
        try:
            actionId = self.addAction('config')
            self._cursor.execute("SELECT configValue FROM Config WHERE configName = %s;",(configName))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self.addStatus(engineId, actionId, 'CONFIG NEW:\t%s\t%s\t%s' % (engineId, configName, configValue))
                self._cursor.execute("INSERT INTO Config (configName, configValue) VALUES (%s, %s);",(configName, configValue))

            else:
                oldValue = rows[0]['configValue']
                if (oldValue != configValue):
                    self.addStatus(engineId, actionId, 'CONFIG CHANGE:\t%s\t%s\t%s\t%s' % (engineId, configName, oldValue, configValue))
                    self._cursor.execute("UPDATE Config SET configValue = %s WHERE configName = %s;",(configValue, configName))

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, configName, configValue, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, configName, configValue, sys.exc_info()[0]))

        finally:
            self._con.commit()

    def getConfig(self, configName):
        """ 
        """
        fName = 'getConfig'
        try:
            self._cursor.execute("SELECT configValue FROM Config WHERE configName = %s;",(configName))
            rows = self._cursor.fetchall()
            configValue = 'n/a'
            if len(rows) > 0:
                print(rows, len(rows))
                configValue = rows[0]['configValue']

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, configName, configValue, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, configName, configValue, sys.exc_info()[0]))

        finally:
            return configValue

    def addEngine(self, engineTitle, engineVersion, engineDescr):
        """ 
        """
        fName = 'addEngine'
        #print(fName, engineTitle, engineVersion,)
        rowId = 0
        try:
            self._cursor.execute("SELECT EngineId FROM Engines WHERE EngineName = %s AND EngineVersion = %s;",(engineTitle, str(engineVersion)))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("INSERT INTO Engines (EngineName, EngineVersion, EngineDesc) VALUES (%s, %s , %s);",(engineTitle, str(engineVersion), engineDescr))
                rowId = self._cursor.lastrowid
            else:
                row = rows[0]
                rowId = int(row['EngineId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, engineTitle, engineVersion, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, engineTitle, engineVersion, sys.exc_info()[0]))

        finally:
            return rowId

    def getEngineDisabled(self, engineId):
        """
        """
        fName = 'getEngineDisabled'
        #print(fName,engineId,)
        engineDisabled = True
        try:
            self._cursor.execute("SELECT EngineDisabled FROM Engines WHERE EngineId = %s;",(engineId))
            rows = self._cursor.fetchall()

            if len(rows) > 0:
                #print('\thaz row\t',)
                row = rows[0]
                engineDisabled = bool(row[0])

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, engineId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, engineId, sys.exc_info()[0]))

        finally:
            #print(engineDisabled)
            return engineDisabled

    def addEngineAction(self, engineId, actionName, actionFunction, actionParams):
        """ Will add an action if not in the database, and return the actionId.
        """
        fName = 'addEngineAction'
        #print('%s>>\t%s\t%s\t%s\t%s' % (fName, engineId, actionName, actionFunction, actionParams))
        rowId = 0
        try:
            actionId = self.addAction(actionName)

            self._cursor.execute("SELECT engineActionId FROM EngineActions WHERE engineId = %s AND actionId = %s AND actionFunction = %s;", (engineId, actionId, actionFunction))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("INSERT INTO EngineActions (engineId, actionId, actionFunction, actionParams) VALUES (%s, %s, %s, %s);",(engineId, actionId, actionFunction, actionParams))
                rowId = self._cursor.lastrowid
            else:
                row = rows[0]
                rowId = int(row[0])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionName, actionFunction, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionName, actionFunction, sys.exc_info()[0]))

        finally:
            return rowId

    def getEngineActionDisabled(self, engineId, actionName, actionFunction):
        """
        """
        fName = 'getEngineActionDisabled'
        #print(fName,)
        engineDisabled = True

        try:
            actionId = self.addAction(actionName)
            #print('\t%s\t%s\t%s\t%s' % (engineId, actionName, actionId, actionFunction))
            self._cursor.execute("SELECT engineActionDisabled FROM EngineActions WHERE engineId = %s AND actionId = %s AND actionFunction = %s;", (engineId, actionId, actionFunction))
            rows = self._cursor.fetchall()

            if len(rows) > 0:
                row = rows[0]
                engineDisabled = bool(row[0])

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, engineId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, engineId, sys.exc_info()[0]))

        finally:
            #print('\t%s' % engineDisabled)
            return engineDisabled

    def addAction(self, actionName):
        """ Will add a new action, at a high level
        """
        fName = 'addAction'
        #print('%s>>\t%s' % (fName, actionName),)
        rowId = -1
        try:
            self._cursor.execute("SELECT actionId FROM Actions WHERE actionName = %s;", [actionName])
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                #print('\tNew\t',)
                self._cursor.execute("INSERT INTO Actions (actionName) VALUES (%s);",[actionName])
                rowId = self._cursor.lastrowid
            else:
                #print('\tExist\t',)
                row = rows[0]
                rowId = int(row['actionId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, actionName, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, actionName, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return rowId

    def addItem(self, engineId, itemURI, itemDate, *args):
        """ adds an item to the database, and create the action links as needed
        """
        fName = 'addItem'
        #print(fName)
        rowId = -1
        try:
            self._cursor.execute("SELECT itemId FROM Items WHERE ItemURI = %s;",[itemURI])
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("INSERT INTO Items (ItemURI, EngineId, ItemDTS) VALUES (%s, %s , %s);",(itemURI, engineId, itemDate))
                rowId = self._cursor.lastrowid
            else:
                row = rows[0]
                rowId = int(row['itemId'])

            # for each of these args, we need to add an action
            for each in args:
                # does this action exist in the db?
                # if not add it in
                for value in each:
                    #print(value)
                    actionId = self.addAction(value)
                    self.addItemEvent(engineId, actionId, rowId)

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, engineId, itemURI, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, engineId, itemURI, sys.exc_info()[0]))

        finally:
            return rowId

    def addNewItem(self, engineId, itemURI, itemDate, *args):
        """ adds an item to the database, and create the action links as needed
        """
        fName = 'addNewItem'
        #print(fName)
        rowId = -1
        try:
            self._cursor.execute("SELECT itemId FROM Items WHERE ItemURI = %s;",[itemURI])
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("INSERT INTO Items (ItemURI, EngineId, ItemDTS) VALUES (%s, %s , %s);",(itemURI, engineId, itemDate))
                rowId = self._cursor.lastrowid

                # for each of these args, we need to add an action
                for each in args:
                    # does this action exist in the db?
                    # if not add it in
                    for value in each:
                        #print(value)
                        actionId = self.addAction(value)
                        self.addItemEvent(engineId, actionId, rowId)

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, engineId, itemURI, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, engineId, itemURI, sys.exc_info()[0]))

        finally:
            return rowId

    def getItemURI(self, itemId):
        """
        """
        fName = 'getItemURI'
        #print(fName)
        itemURI = ''
        try:
            self._cursor.execute("SELECT itemURI FROM Items WHERE ItemId = %s;",[itemId])
            rows = self._cursor.fetchall()

            if len(rows) > 0:
                row = rows[0]
                itemURI = row['itemURI']

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, itemId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, itemId, sys.exc_info()[0]))

        finally:
            return itemURI

    def addLinkType(self, linkType):
        """ Will add a link to show how the left and right elements are
            connected.
        """
        fName = 'addLinkType'
        #print(fName)
        rowId = -1
        try:
            self._cursor.execute("SELECT LinkTypeId FROM LinkTypes WHERE LinkTypeName = %s;",[linkType])
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("INSERT INTO LinkTypes (LinkTypeName) VALUES (%s);",[linkType])
                rowId = self._cursor.lastrowid
            else:
                row = rows[0]
                rowId = int(row['LinkTypeId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, linkType, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, linkType, sys.exc_info()[0]))

        finally:
            return rowId

    def addItemLink(self, engineId, itemIdLeft, itemIdRight, linkType = 'contains'):
        """ Will add a link to show how the left and right elements are
            connected.
        """
        fName = 'addItemLink'
        #print('%s>>\t%s\t%s\t%s\t%s\t' % (fName, engineId, itemIdLeft, itemIdRight, linkType),)
        rowId = -1
        try:
            linkTypeId = self.addLinkType(linkType)
            #print(linkTypeId,)

            self._cursor.execute("SELECT itemLinkId FROM ItemLinks WHERE itemId_Left = %s AND itemId_right = %s AND linkTypeId = %s;",(itemIdLeft, itemIdRight, linkTypeId))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                #print('\tNew\t',)
                self._cursor.execute("INSERT INTO ItemLinks (EngineId, itemId_left, itemId_right, linkTypeId, itemLinkDTS) VALUES (%s, %s , %s, %s , %s);",(engineId, itemIdLeft, itemIdRight, linkTypeId, datetime.datetime.now()))
                rowId = self._cursor.lastrowid
            else:
                #print('\tExist\t',)
                row = rows[0]
                rowId = int(row['itemLinkId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s, %s):\t%s" % (fName, engineId, itemIdLeft, itemIdRight, linkType, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s, %s):\t%s" % (fName, engineId, itemIdLeft, itemIdRight, linkType, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return rowId

    def getItemChildren(self, itemId_left, itemData, linkType = 'contains'):
        """ this will perform a mixed bag of queries, the aim is to return a
            list of companies that need to have their uri resolved.
            The way this works is as follows:
            Grab all the records ItemData = <itemData>
                For each of these, grab the itemURI, if the itemID is a child of ItemLink.ItemID_Left
                If there is no ItemRecord that is a child of itemId_left, then these are the ones we
                want returned.
                bear in mind there will be many can potentially be many companyName duplicated
        """
        fName = 'getItemChildren'
        #print('%s>>\t%s\t%s\t%s\t' % (fName, itemId_left, itemData, linkType),)
        itemList = []
        try:
            linkTypeId = self.addLinkType(linkType)
            #print(linkTypeId,)

            self._cursor.execute("""
select id.ItemDataValue as ItemDataValue
from ItemData id
where id.ItemData = %s
and id.itemDataValue not in (
    select id.ItemDataValue
    from ItemLinks il inner join Items i
        on il.itemId_right = i.itemId
        inner join ItemData id on i.ItemId = id.itemId
            and id.ItemData = %s
    where il.itemId_left = %s
    and il.linkTypeId = %s
    group by id.ItemDataValue
)
group by id.ItemDataValue
order by id.ItemDataValue;""",(itemData, itemData, itemId_left, linkTypeId))
            rows = self._cursor.fetchall()

            if len(rows) > 0:
                #print('\tNew\t',)
                for row in rows:
                    itemList.append(row['ItemDataValue'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, itemId_left, itemData, linkType, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, itemId_left, itemData, linkType, sys.exc_info()[0]))

        finally:
            print
            return itemList


    def addItemEvent(self, engineId, actionId, itemId):
        """ Will add an event to the specified item.
        """
        fName = 'addItemEvent'
        #print('%s>>\t%s\t%s\t%s\t' % (fName, engineId, actionId, itemId),)
        #Error in addItemEvent(-, 5, 21, 1150684):	1205
        rowId = -1
        try:
            self._cursor.execute("SELECT ItemEventId FROM ItemEvents WHERE engineId = %s AND actionId = %s AND ItemId = %s;",(engineId, actionId, itemId))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                #print('\tNew\t',)
                self._cursor.execute("INSERT INTO ItemEvents (engineId, actionId, itemId, itemEventAddedDate) VALUES (%s, %s, %s , %s);",(engineId, actionId, itemId, datetime.datetime.now()))
                rowId = self._cursor.lastrowid
            else:
                #print('\tExist\t',)
                row = rows[0]
                rowId = int(row['ItemEventId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionId, itemId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, engineId, actionId, itemId, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return rowId


    def addItemData(self, itemId, itemData, itemDataValue, itemDataSeq):
        """ Will add an a data tag and value for a particular item...
        """
        fName = 'addItemData'
        #print('%s>>\t%s\t%s\t%s\t' % (fName, itemId, itemData, itemDataSeq),)
        rowId = -1
        try:            
            self._cursor.execute("SELECT ItemDataId FROM ItemData WHERE ItemId = %s AND ItemData = %s AND ItemDataSeq = %s;",(itemId, itemData, itemDataSeq ))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                #print('\tNew\t',)
                self._cursor.execute("INSERT INTO ItemData (itemId, itemData, itemDataValue, itemDataSeq, itemDataAdded) VALUES (%s, %s , %s, %s , %s);",(itemId, itemData, itemDataValue, itemDataSeq, datetime.datetime.now()))
                rowId = self._cursor.lastrowid
            else:
                #print('\tExist\t',)
                row = rows[0]
                rowId = int(row['ItemDataId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s, %s):\t%s" % (fName, itemId, itemData, itemDataSeq, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, itemId, itemData, itemDataSeq, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return rowId

    def getItemData(self, itemData, itemDataSeq = 0):
        """ returns the itemValue at the specified sequence
        """
        fName = 'getItemData'
        #print('%s>>\t%s\t%s\t%s\t' % (fName, itemValue, itemDataSeq),)
        rowId = -1
        try:
            self._cursor.execute("SELECT ItemId FROM ItemData WHERE ItemData = %s AND ItemDataSeq = %s;",(itemData, itemDataSeq ))
            rows = self._cursor.fetchall()

            if len(rows) > 0:
                row = rows[0]
                rowId = int(row['ItemId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, itemData, itemDataSeq, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, itemData, itemDataSeq, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return rowId

    def getItemDataValues(self, itemData):
        """ returns the itemValue at the specified sequence
        """
        fName = 'getItemDataValues'
        itemDataValues = []
        
        #print('%s>>\t%s\t%s\t%s\t' % (fName, itemValue, itemDataSeq),)

        try:
            self._cursor.execute("SELECT ItemDataValue FROM ItemData WHERE ItemData = %s GROUP BY ItemDataValue ORDER BY ItemDataValue;",(itemData))
            rows = self._cursor.fetchall()

            for row in rows:
                itemDataValues.append(row['ItemDataValue'])

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, itemData, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, itemData, sys.exc_info()[0]))

        finally:
            #print(rowId)
            return itemDataValues

    def getItemDataList(self, itemId, itemData):
        """ returns the itemValue at the specified sequence
        """
        fName = 'getItemDataList'
        itemDataValues = []

        #print('%s>>\t%s\t%s\t' % (fName, itemId, itemData),)
        try:
            self._cursor.execute("SELECT itemDataValue FROM ItemData WHERE ItemId = %s AND ItemData = %s ORDER BY itemDataValue;",(itemId, itemData ))
            rows = self._cursor.fetchall()

            for row in rows:
                itemDataValues.append(row['itemDataValue'])

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, itemId, itemData, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, itemId, itemData, sys.exc_info()[0]))

        finally:
            return itemDataValues

    def getItemDataAll(self, itemId):
        """ returns the itemValue at the specified sequence
        """
        fName = 'getItemDataList'
        itemDataValues = []

        #print('%s>>\t%s\t%s\t' % (fName, itemId, itemData),)
        try:
            self._cursor.execute("SELECT itemData, itemDataValue FROM ItemData WHERE ItemId = %s ORDER BY itemDataAdded;", [itemId])
            rows = self._cursor.fetchall()

            for row in rows:
                itemDataValues.append(row)

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, itemId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, itemId, sys.exc_info()[0]))

        finally:
            return itemDataValues
            
    def getItemList(self, engineId, actionName, findOthers = False, timeSpan = -3):
        """ will look for itemEvents that have the actionName
            for each item it will check for eventdate is null and engineId
                it will create engineId record if missing

            it will return a list of tuples itemId, itemURI
        """
        fName = 'getItemList'
        items = []

        try:
            # first create missing records...
            actionId = self.addAction(actionName)
            
            if findOthers:
                self._cursor.execute("""
                    SELECT i.ItemID AS ItemID, ItemURI
                        FROM Items i 
                            INNER JOIN ItemEvents e 
                                ON i.itemId = e.itemId
                                AND e.actionId = %s
                        WHERE i.ItemId NOT IN (
                            SELECT ItemId
                            FROM ItemEvents ie
                            WHERE 
                                ie.ItemEventDate IS NOT NULL
                            AND
                                ie.actionId = %s
                            AND
                                ie.engineId = %s
                        )
                        AND e.ItemEventAddedDate >= DATE_ADD(NOW(), INTERVAL %s MONTH)
                        GROUP BY i.ItemID, ItemURI;""",(actionId, actionId, engineId, timeSpan))
                
            else:
                # next grab the unfinished records
                self._cursor.execute("""
                    SELECT i.ItemID AS ItemID, ItemURI
                        FROM Items i 
                            INNER JOIN ItemEvents e 
                                ON i.itemId = e.itemId
                                AND e.actionId = %s
                                AND e.engineId = %s
                        WHERE e.ItemEventAddedDate >= DATE_ADD(NOW(), INTERVAL %s MONTH)
                        AND e.ItemEventDate IS NULL;""",(actionId, engineId, timeSpan))
                
            rows = self._cursor.fetchall()
            
            for row in rows:
                items.append((row['ItemID'], row['ItemURI']))

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, engineId, actionName, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, engineId, actionName, sys.exc_info()[0]))

        finally:
            return items

    def updateItem(self, engineId, itemId, actionId, itemEventDate):
        """ For the specified itemId and engineId it will update the itemEvent record
        """
        fName = 'updateItem'

        #print('%s>>\t%s\t%s\t%s\t%s\t' % (fName, engineId, itemId, actionId, itemEventDate))
        try:
            # does the engine / action exist
            self._cursor.execute("SELECT ItemEventId FROM ItemEvents WHERE engineId = %s AND actionId = %s AND ItemId = %s;",(engineId, actionId, itemId))
            rows = self._cursor.fetchall()

            if len(rows) == 0:
                self._cursor.execute("""INSERT INTO ItemEvents 
                (itemEventDate, engineId, itemId, actionId, ItemEventAddedDate) 
                VALUES (%s, %s, %s, %s, %s);""",(itemEventDate, engineId, itemId, actionId, datetime.datetime.now()))
            else:            
                self._cursor.execute("""UPDATE ItemEvents 
                SET itemEventDate = %s 
                WHERE engineId = %s AND itemId = %s AND actionId = %s;""",(itemEventDate, engineId, itemId, actionId))

        except:
            print("\tUnexpected error in %s(-, %s, %s, %s):\t%s" % (fName, engineId, itemId, actionId, sys.exc_info()[0]))
            return False

        return True

    def getEngineActionList(self, engineId):
        """ returns the itemValue at the specified sequence
        """
        fName = 'getEngineActionList'
        itemDataValues = []

        #print('%s>>\t%s\t' % (fName, engineId),)
        try:
            self._cursor.execute("select e.engineId AS engineId, a.actionId, a.actionName, ea.actionFunction, actionParams, count(*) as itemCount from Engines e inner join EngineActions ea on e.engineID = ea.engineID inner join Actions a on ea.actionID = a.actionID inner join ItemEvents ie on e.engineId = ie.engineId and a.actionId = ie.actionId where e.engineDisabled = 0 and ea.engineActionDisabled = 0 and ie.itemEventDate IS NULL and e.egnineId = %s group by e.engineId, a.actionId, a.actionName, ea.actionFunction, actionParams order by e.engineId, a.actionId, a.actionName, ea.actionFunction, actionParams limit 1;",[engineId])
            rows = self._cursor.fetchall()

            for row in rows:
                itemDataValues.append(row['engineId'])

        except mdb.Error as e:
            print("\tError in %s(-, %s):\t%s" % (fName, engineId, e.args[0]))

        except:
            print("\tUnexpected error in %s(-, %s):\t%s" % (fName, engineId, sys.exc_info()[0]))

        finally:
            return itemDataValues

    def getItemTree(self, engineId, itemId, recursive = True):
        """ returns a dictionary of items under the specified itemId from the
            itemLinks table... This is recursive unless spcified
        """
        fName = 'getItemTree'
        itemValues = dict()

        #print('%s>>\t%s\t%s\t' % (fName, engineId, itemId),)
        try:
            sql = 'CALL proc_ItemTree(%s)' % itemId
            self._cursor.execute(sql)
            rows = self._cursor.fetchall()
            #print(len(rows))

            # pop the cursor here as for some reason it'll trigger a 2014 mysql error
            self._cursor.close()
            self._cursor = self._con.cursor()

            for row in rows:
                # http://answers.oreilly.com/topic/156-how-to-identify-null-values-in-result-sets-in-mysql/
                row = list (row)  # convert nonmutable tuple to mutable list
                for i in range (0, len (row)):
                    if row[i] == None:  # is the column value NULL?
                          row[i] = "NULL"

                print(row)
                itemValues.update({'%s' % row[0]: (row[1], row[2], row[3])}) #, row[2], row[3])})

        except mdb.Error as e:
            print("\tError in %s(-, %s, %s):\t%s" % (fName, engineId, itemId, e))

        except Exception as e:
            print("\tUnexpected error in %s(-, %s, %s):\t%s" % (fName, engineId, itemId, e))

        finally:

            return itemValues


def main():
    import configparser
    import os

    obj = PeregrinDB()

    # the following is a hack to allow me to load mods and classes from a filepath
    modPath = os.path.dirname(__file__)
    corepath = os.path.split(modPath)[0]
    cfg_path = os.path.join(corepath, 'config', 'PeregrinDaemon.cfg')
    print('Config Path: {0}'.format(cfg_path))

    # configuration details
    config = configparser.RawConfigParser()
    config.readfp(open(cfg_path))
    for each_section in config:
        print('Section: {0}'.format(each_section))
        for (each_key, each_val) in config.items(each_section):
            print('\t{0} => {1}'.format(each_key, each_val))

    # database, details in the config file
    obj.connect_db(config)

    actionId = obj.addAction('Status')
    obj.addStatus(obj._engine_id, actionId, 'Hello this is a status message')
    status = obj.getStatus()
    for row in status:
        print(row)

    configName = 'test01'
    obj.addConfig(obj._engine_id, configName, 'value01')
    print(obj.getConfig(configName))
    obj.addConfig(obj._engine_id, configName, 'value02')
    print(obj.getConfig(configName))

    status = obj.getStatus()
    for row in status:
        print(row)

    runQueue = obj.getConfig('RunQueue')
    print(runQueue)
    if runQueue == 'n/a':
        print('Add runQueue')
        obj.addConfig(obj._engine_id, 'RunQueue', 1)
        runQueue = obj.getConfig('RunQueue')

    print('{}\t{}'.format(runQueue, (runQueue == '1')))
    obj.addConfig(obj._engine_id, 'RunQueue', 0)
    runQueue = obj.getConfig('RunQueue')
    print('{}\t{}'.format(runQueue, (runQueue == '1')))
    obj.addConfig(obj._engine_id, 'RunQueue', 1)

    print(obj.info())

    status = obj.getStatus()
    for row in status:
        print(row)

    del obj
    return 0

if __name__ == '__main__':
    sys.exit(main())