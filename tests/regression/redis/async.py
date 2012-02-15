import os

from stdnet.lib import redis
from stdnet import test, getdb
from stdnet.conf import settings

from examples.models import SimpleModel

from .base import TestCase

skipUnless = test.unittest.skipUnless

def makeredis(pool = None):
    from stdnet.lib.redis.async import AsyncRedisConnection
    cursor = getdb(format(settings.DEFAULT_BACKEND), decode = 1,
                   connection_class = AsyncRedisConnection)
    return cursor.client
    

skipUnless(os.environ['stdnet_test_suite'] == 'pulsar','Requires pulsar')
class RedisCommands(TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.client = makeredis()
        
    def get_client(self, pool = None, build = False):
        return self.client

    def __test_get_and_set(self):
        yield self.async.assertTrue(self.client.set('a','ciao'))
        yield self.async.assertEquals(self.client.get('a'), b'ciao')
        
    def __test_delete(self):
        yield self.async.assertFalse(self.client.delete('a'))
        yield self.async.assertTrue(self.client.set('a','foo'))
        yield self.async.assertTrue(self.client.delete('a'))
        
        
skipUnless(os.environ['stdnet_test_suite'] == 'pulsar','Requires pulsar')
class AsyncStdnet(TestCase):
    model = SimpleModel
    
    def backend_params(self):
        from stdnet.lib.redis.async import AsyncRedisConnection
        return {'connection_class': AsyncRedisConnection}
    
    def testcreate(self):
        m = SimpleModel(code = 'bla').save()
        
    
    