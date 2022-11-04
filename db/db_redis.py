import redis
from redis.exceptions import RedisError


def connect_redis():
    try:
        r = redis.Redis(host='localhost', port=6380, db=0, socket_timeout=1)
        r.ping()
        return r
    except RedisError:
        return None
