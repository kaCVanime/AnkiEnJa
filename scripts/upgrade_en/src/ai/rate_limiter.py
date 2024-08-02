from limits import strategies, parse_many, storage
from functools import wraps
from time import sleep
from loguru import logger
from threading import Lock
from datetime import datetime


lock = Lock()


memory_storage = storage.MemoryStorage()
limiter = strategies.FixedWindowRateLimiter(memory_storage)

second, minute, day = parse_many('1/second;15/minute;1500/day')

def check():
    return limiter.test(second) and limiter.test(minute) and limiter.test(day)

def log_stats():
    if limiter.test(second, 'stats_log_limit'):
        limiter.hit(second, 'stats_log_limit')
        limiters = [day, minute, second]
        for l in limiters:
            if not limiter.test(l):
                reset, _ = limiter.get_window_stats(l)
                logger.warning("reset at {}", datetime.fromtimestamp(reset))


def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while True:
            lock.acquire(timeout=60)
            logger.debug('lock acquired')

            if check():
                break

            log_stats()

            logger.debug('lock released')
            lock.release()
            logger.debug('sleeping')
            sleep(1)

        logger.debug('executing {}', func.__name__)

        for r in (second, minute, day):
            assert limiter.hit(r)

        result = func(*args, **kwargs)

        lock.release()
        logger.debug('lock released after executing')

        return result

    return wrapper
