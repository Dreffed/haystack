# -*- coding: utf-8 -*-
# pylint: disable=too-many-instance-attributes
# pylint: disable=invalid-name
#           invalid constant name convention
"""

@project: Peregrin (Haystack)
@author: david gloyn-cox
"""
import os
import time
import random
import timeit
from datetime import datetime

class PeregrinBase(object):
    """ This is the base class for the Peregrin Haystack Crawler."""
    def __init__(self):
        self._title = 'Base Class'
        self._version = '0.0'
        self._descr = 'Base Class for Peregrin.'
        self._engine_id = -1
        self._state = 'Initialized'
        self._uri = ''
        self._items = 0
        self._db = None
        self._config = None
        self.item_id = None
        self._actions = {}

    def state(self):
        """ Returns the state of the engine"""
        return self._state

    def info(self):
        """ returns the objects information"""
        return (self._title, self._version, self._descr)

    def get_id(self):
        """Returns the engine id, this is normally obtained
        from the database."""
        return self._engine_id

    def set_id(self, engine_id):
        """Allows the user to overrider the engine id, this
        will not update the underlying database value."""
        self._engine_id = engine_id

    def set_db(self, db_obj):
        """ if this is declared the calling program will pass in the
        cursor from the exisiting db """
        self._db = db_obj
        if self._engine_id == -1:
            self._engine_id = self._db.addEngine(self._title, self._version, self._descr)
            self._db.commit_db()

    def set_config(self, config):
        """ pass in the configuration file and then call config
        to load the new data."""
        self._config = config
        self.init()

    def init(self):
        """ will initialize the system to run the class """
        self._state = 'Initializing...'
        self.item_id = self._db.getItemData(self._title)
        self.actions()

        if self._title in self._config:
            # if we have a title here, we can now pull the values...
            settings = self._config[self._title]

            if 'uri' in settings:
                # the uri is the base element of the object...
                self.item_id = self._db.addItem(self._engine_id, settings['uri'], datetime.now())
                self._db.addItemData(self.item_id, self._title, settings['uri'], 0)

            if 'data' in settings:
                # data element is a list of objects
                #   name: value: id
                for data_element in settings['data']:
                    self._db.addItemData(
                        self.item_id,
                        data_element['name'],
                        data_element['value'],
                        data_element['id'])

            self._db.commit_db()

        self._state = 'Ready'

    def actions(self):
        """ Returns a list of action and state this object can perform...
            These are in a form that Peregrin can handle, and are use
            by the class to limit what it allows Peregrin to call.

            The acton dictionary is as follows:
                Key: the name of the functin to call
                Value Tuple:
                    ActionName: the action name to fetch on values
                    ParamList: A list of ItemData Values to return
                        This will only return entries that have all values populated.
        """
        # add action functions to the action dictionary
        # self._actions['function_name'] = ('<action_name>', None | [...])

        return self._actions

    def start(self):
        """This is to be overrided by the inheriting class
        This method initialize the run run and runaction functions,
         and if wanted run in a thread."""
        self._state = 'Starting'
        self.run()

    def stop(self):
        """This is to be overrided by the inheriting class"""
        self._state = 'Stopping'

    def run(self):
        """ This acts as the marshalling function, this will call the relevant
        functions as defined in actions against the database...

        The sequence is...
            if ItemEvents are there then we process them, otherwise we call the generic
            getItemss function
        """
        self._state = 'Running...'
        for func_name, action in self._actions.items():
            action_name, action_params = action
            if action_params is None:
                print('Running %s.%s' % (self._title, func_name))
                func = getattr(self, func_name)
                func()
            else:
                self.runAction(action_name, func_name)

        self._db.commit_db()
        self._state = 'Waiting'

    def runAction(self, action_name, func_name):
        """ will run the action specifiec in the action name
        """
        item_data_list = self._db.getItemList(self._engine_id, action_name)
        action_id = self._db.addAction(action_name)
        func = getattr(self, func_name)
        print('Running %s.%s' % (self._title, func_name))

        i = 0
        total = len(item_data_list)
        start_time = timeit.default_timer()

        for item_id, item_url in item_data_list:
            i += 1
            func(item_url)
            self._db.updateItem(self._engine_id, item_id, action_id, datetime.now())

            if i % 1000 == 0:
                step = ((timeit.default_timer() - start_time) / i)
                eta = step * (total - i)
                print('Processing: %s / %s ETA: %ss at %s' % (i, total, eta, step))

                if self._db != None:
                    self._db.commit_db()

                runQueue = self._db.getConfig('RunQueue')
                if runQueue == 0:
                    break

            time.sleep(random.randint(1, 10))

        self._db.commit_db()

def load_class(module_obj, class_name=None):
    """load the first or named class from a loaded
    module, it is a helper function."""
    import inspect

    class_members = inspect.getmembers(module_obj, inspect.isclass)

    class_obj = None

    for cls_obj in class_members:
        if class_name is None or cls_obj[0] == class_name:
            print('Class:\t{0}'.format(cls_obj[0]))
            class_obj = cls_obj[1]()
            break

    return class_obj

def load_module(module_name, module_path, class_name=None):
    """This will load a module from a filepath and then
    will return the named or first class in the
    module."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module_obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module_obj)
    return load_class(module_obj, class_name)

def main(loader_config):
    """The main function will initialize the class
    and run it as part of the peregrin framework."""
    import sys
    import configparser

    # the following is a hack to allow me to load mods and classes from a filepath
    db_module_path = os.path.join(loader_config['path'],
            loader_config['db']['path'],
            loader_config['db']['name'])

    # shed the 2nd part of the split not used later or needed
    db_module_name = os.path.splitext(os.path.split(db_module_path)[-1])[0]
    db_class = load_module(db_module_name, db_module_path)

    # configuration details
    cfg_path = os.path.join(loader_config['path'],
            loader_config['config']['path'],
            loader_config['config']['name'])

    config = configparser.RawConfigParser()
    with open(cfg_path) as f:
        config.read_file(f)

    # database, details in the config file
    if hasattr(db_class, 'connect_db') and db_class:
        print('\tConnecting to database...')
        db_class.connect_db(config)
        print('\tEngine ID:\t{0}'.format(db_class.get_id()))
        obj_title, obj_version, obj_descr = db_class.info()
        print('\t{0}:\t{1}\n\t\t{2}'.format(obj_title, obj_version, obj_descr))

    # create the object
    if 'module' in loader_config:
        obj = load_class(loader_config['module'], loader_config['name'])

    else:
        # no module defined so search the current module
        obj = load_class(sys.modules[__name__], loader_config['name'])

    if obj:
        if hasattr(obj, 'set_db'):
            obj.set_db(db_class)

        obj.set_config(config)

        print('\tEngine ID:\t{0}'.format(obj.get_id()))
        obj_title, obj_version, obj_descr = obj.info()
        print('\t{0}:\t{1}\n\t\t{2}'.format(obj_title, obj_version, obj_descr))
        act_list = obj.actions()

        print('\tActions:')
        if len(act_list) > 0:
            for a in act_list:
                print('\t\t{0}'.format(a))
        else:
            print('\t\tNo actions defined!')

        obj.init()
        print('\tRunning >> {0}'.format(datetime.today()))

        obj.start()
        print('\tItemId:\t%s\t[%s]' % (obj.item_id, obj.get_id()))

        time.sleep(random.randint(1, 10))

        obj.stop()

        print('\tEnding >> {0}'.format(datetime.today()))
        del obj

    del db_class
    del config

    print('================================================')

    return 0

if __name__ == '__main__':
    config_data = {}
    modPath = os.path.dirname(__file__)
    config_data['path'] = os.path.split(modPath)[0]
    config_data['name'] = 'PeregrinBase'

    config_data['db'] = {}
    config_data['db']['path'] = 'db'
    config_data['db']['name'] = 'PeregrinDB.py'

    config_data['config'] = {}
    config_data['config']['path'] = 'config'
    config_data['config']['name'] = 'PeregrinDaemon.cfg'

    cls_name = 'PeregrinBase'
    config_data[cls_name] = {}
    config_data[cls_name]['uri'] = '...base class...'
    config_data[cls_name]['data'] = []
    config_data[cls_name]['data'].append({'name': 'base', 'value': 'base', 'id': -1})

    main(config_data)
