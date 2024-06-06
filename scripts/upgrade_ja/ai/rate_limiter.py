from limits import strategies, parse_many, storage
from functools import wraps
from time import sleep

memory_storage = storage.MemoryStorage()
limiter = strategies.FixedWindowRateLimiter(memory_storage)

second, minute, day = parse_many('1/3seconds;15/minute;1500/day')


def check():
    return limiter.test(second) and limiter.test(minute) and limiter.test(day)


def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        while not check():
            sleep(0.1)

        for r in (second, minute, day):
            assert True is limiter.hit(r)

        return func(*args, **kwargs)

    return wrapper
