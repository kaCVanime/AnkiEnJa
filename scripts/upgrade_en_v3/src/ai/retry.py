from functools import wraps
from time import sleep
from loguru import logger

def retry(max_retries, delay=1):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    logger.warning(f"Attempt {retries} failed: {e}")
                    sleep(delay)
                    last_error = e
            raise Exception(last_error)

        return wrapper

    return decorator_retry
