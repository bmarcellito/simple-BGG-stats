from time import sleep
import gc

from my_logger import logger


def extra_admin() -> None:
    while True:
        logger.info(f'Garbage col: {gc.get_count()}')
        gc.collect()
        sleep(60*30)