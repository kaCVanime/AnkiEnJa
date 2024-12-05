from functools import wraps
from time import sleep
from loguru import logger
import os

def retry(max_retries, delay=1, exit_errors=None, stop_errors=None):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            last_error = None
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if exit_errors and type(e) in exit_errors:
                        print(f"\nEncounter exit error: {type(e).__name__}")
                        logger.error(e)
                        os._exit(1)

                    if stop_errors and type(e) in stop_errors:
                        raise e

                    retries += 1
                    logger.warning(f"Attempt {retries} failed: {e}")
                    sleep(delay)
                    last_error = e
            raise Exception(last_error)

        return wrapper

    return decorator_retry
