'''\
A specialized test case class for stdnet
'''
import os
import sys
import logging
from inspect import isclass

import sys

if sys.version_info >= (2,7):
    import unittest
else:
    try:
        import unittest2 as unittest
    except ImportError:
        print('To run tests in python 2.6 you need to install\
 the unitest2 package')
        exit(0)

from stdnet import orm, getdb, BackendRequest
from stdnet.utils import gen_unique_id


class TestCase(unittest.TestCase):
    '''A :class:`unittest.TestCase` subclass for testing stdnet. It contains
some utility functions for tesing in a parallel test suite.

.. attribute:: backend

    A :class:`stdnet.BackendDataServer` for the :class:`TestCase`.
    It is different for each instance and it is created just before
    :meth:`setUp` method is called.
'''    
    models = ()
    model = None
    
    def backend_params(self):
        '''Optional backend parameters'''
        return {}
    
    def session(self, **kwargs):
        '''Create a new :class:`stdnet.orm.Session` bind to the
:attr:`TestCase.backend` attribute.'''
        session = orm.Session(self.backend, **kwargs)
        self.assertEqual(session.backend, self.backend)
        return session
    
    def register(self):
        '''Utility for registering the managers to the current backend.
This should be used with care in parallel testing. All registered models
will be unregistered after the :meth:`tearDown` method.'''
        for model in self.models:
            orm.register(model, self.backend)
    
    def clear_all(self):
        return self.backend.flush(pattern = self.prefix + '*')
    
    def _pre_setup(self):
        if not self.models and self.model:
            self.models = (self.model,)
        if not self.model and self.models:
            self.model = self.models[0]
        self.prefix = 'stdnet-test-'+gen_unique_id()+'.'
        self.backend = getdb(prefix = self.prefix, **self.backend_params())
        r = None
        if self.backend.name == 'redis':
            r = self.backend.client.script_flush()
        if isinstance(r, BackendRequest):
            return r.add_callback(lambda r: self.clear_all())
        else:
            return self.clear_all()
    
    def load_scripts(self):
        if self.backend.name == 'redis':
            self.backend.load_scripts()
            
    def _post_teardown(self):
        session = orm.Session(self.backend)
        self.clear_all()
        orm.unregister()
    
    def __call__(self, result=None):
        """Wrapper around default __call__ method
to perform cleanup, registration and unregistration.
        """
        self._pre_setup()
        super(TestCase, self).__call__(result)
        self._post_teardown()
    
        

 