import asyncio
from functools import wraps
import logging
import random

from django.conf import settings

from uvicorn.logging import ColourizedFormatter


# Various base classes
logger = logging.getLogger(__name__)


class TomatoAuthError(Exception):
    def __init__(self, reason, field=None, should_sleep=False):
        self.field = field
        self.should_sleep = should_sleep
        super().__init__(reason)


async def retry_on_failure(coro, *args, **kwargs):
    running = True
    try_num = 1
    while running:
        try:
            logger.debug(f"Running try #{try_num + 1} of {coro.__name__}()")
            value = await coro(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info(f"Cancelled task {coro.__name__}()")
            running = False
        except Exception:
            sleep_time = random.uniform(0.75, 1.5)
            logger.exception(f"Error in try #{try_num} of {coro.__name__}(), running again in {round(sleep_time, 3)}s")
            try_num += 1
            await asyncio.sleep(sleep_time)
        else:
            logger.debug(f"{coro.__name__}() cleanly exited. Exiting retry loop.")
            return value


RUNNING_TASKS = []


def task(coro):
    @wraps(coro)
    def wrapped(self):
        logger.info(f"Running task {coro.__name__}()")
        RUNNING_TASKS.append(asyncio.create_task(retry_on_failure(coro, self)))

    return wrapped


def init_logger():
    uvicorn_logger = logging.getLogger("uvicorn")
    ws_api_logger = logging.getLogger(__name__).parent
    ws_api_logger.setLevel("DEBUG" if settings.DEBUG else "INFO")
    formats = {
        ws_api_logger: "{asctime} {levelprefix:<8} {message} ({name})",
        uvicorn_logger: "{asctime} {levelprefix:<8} {message} (uvicorn)",
    }

    for logger_to_modify in (uvicorn_logger, ws_api_logger):
        for handler in logger_to_modify.handlers:
            logger_to_modify.removeHandler(handler)
        handler = logging.StreamHandler()
        formatter = ColourizedFormatter(formats[logger_to_modify], style="{")
        handler.setFormatter(formatter)
        logger_to_modify.addHandler(handler)
