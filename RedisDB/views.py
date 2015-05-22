import redis
import itertools

try:
    import cPickle as pickle
except ImportError:
    import pickle 

from config import REDIS_CACHE


class RedisMenager(object):
    """
    Class to MAnage multiple Redis.
    """
    
    no_of_redis = 0
    all_keys = {}
    redis_servers = {}
    for index, db_conf in enumerate(REDIS_CACHE):
        no_of_redis += 1
        redis_conn = redis.StrictRedis(host=db_conf['HOST'],
                         port=db_conf['PORT'], db=db_conf['DB'])
        redis_servers[index] = redis_conn
        for key in redis_conn.keys():
            all_keys[key] = index
    
    def getRedis(self, key):
        """
        Return Which db to be used by key evaluation.
        """
        keyInt = reduce(lambda x, y: x+ord(y), itertools.chain([0], key))
        redisDB = keyInt % self.no_of_redis
        return redisDB

    def getNextRedis(self, redis_client):
        redis_client += 1
        return redis_client % self.no_of_redis

    def get(self, key):
        """
        Retrieve a value from the cache.

        Returns unpickled value if key is found, the default if not.
        """
        redis_client = self.getRedis(key)
        value = self.redis_servers[redis_client].get(key)
        if value is None:
            if key in self.all_keys:
                count = 0
                while count < self.no_of_redis:
                    count += 1
                    redis_client = self.getNextRedis(redis_client)
                    value = self.redis_servers[redis_client].get(key)
                    if value is not None:
                        break 
        if value is None:        
            return False
        try:
            result = int(value)
        except (ValueError, TypeError):
            result = pickle.loads(value)
        return result

    def _set(self, key, value, timeout):
        redis_client = self.getRedis(key)
        self.all_keys[key] = redis_client
        if not timeout:
            return self.redis_servers[redis_client].set(key, value)
        try:
            return self.redis_servers[redis_client].setex(key, int(timeout), value)
        except:
            return False

    def set(self, key, value, timeout=None):
        """
        Persist a value to the cache, and set an optional expiration time.
        """
        try:
            value = float(value)
            # If you lose precision from the typecast to str, then pickle value
            if int(value) != value:
                raise TypeError
        except (ValueError, TypeError):
            result = self._set(key, pickle.dumps(value), int(timeout))
        else:
            result = self._set(key, int(value), timeout)
        # result is a boolean
        return result

        
