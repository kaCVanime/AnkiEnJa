from limits import strategies, parse_many, storage
from functools import wraps
from time import sleep
from loguru import logger
from threading import Lock
lock = Lock()

# logger.remove()
# logger.add('ai.log')

memory_storage = storage.MemoryStorage()
limiter = strategies.FixedWindowRateLimiter(memory_storage)

second, minute, day = parse_many('1/3seconds;15/minute;1500/day')


free = True

def check():
    return limiter.test(second) and limiter.test(minute) and limiter.test(day)


def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        global free

        while True:
            lock.acquire()
            logger.debug('lock acquired')
            free = check()
            logger.debug('free? {}.', free)
            if free:
                break
            logger.debug('lock released')
            lock.release()
            logger.debug('sleeping')
            sleep(1)

        logger.info('executing {}', func.__name__)

        for r in (second, minute, day):
            assert True is limiter.hit(r)
            # limiter.hit(r)

        result = func(*args, **kwargs)

        free = check()

        lock.release()
        logger.debug('lock released after executing')

        return result

    return wrapper
