import redis

class BasicCache(object):
    '''
    Starting simple with an interface I can override when I need fancier functionality
    '''

    def __init__(self):

        self._data = {}

    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, val):
        return self._data.__setitem__(key, val)

    def __contains__(self, key):
        return self._data.__contains__(key)

class RedisCache(object):

    def __init__(self, **kwargs):
        self._r = redis.Redis(
                    host=kwargs.get('host', 'localhost'),
                    port=kwargs.get('port',6379),
                    password=kwargs.get('password',""),
                    )

        self._r.config_set('maxmemory', kwargs.get('maxmemory','2g'))
        self._r.config_set('maxmemory-policy', kwargs.get('maxmemory-policy','volatile-lru'))

    
    def __getitem__(self, key):
        return self._r.get(key)

    def __setitem__(self, key, val):
        return self._r.set(key, val)

    def __contains__(self, key):
        if self[key] is None:
            return False
        else:
            return True

def get_cache(type='redis', **kwargs):

    if type == 'basic':
        return BasicCache(**kwargs)
    elif type == 'redis':
        return RedisCache(**kwargs)
    else:
        raise NotImplemented