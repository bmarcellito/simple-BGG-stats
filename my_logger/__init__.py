import logging
import socket
from logging.handlers import SysLogHandler
import time

import streamlit as st


def timeit(func):
    def timed(*args, **kwargs):
        ts = time.time()
        result = func(*args, **kwargs)
        te = time.time()
        log_text = f'*** Function: {func.__name__}, execution time: {round((te - ts) * 1000, 1)}ms'
        logger.info(log_text)
        return result
    return timed


def getlogger(name):
    class ContextFilter(logging.Filter):
        hostname = socket.gethostname()

        def filter(self, record):
            record.hostname = ContextFilter.hostname
            return True

    # logging.basicConfig(level=logging.INFO)
    syslog = SysLogHandler(address=(st.secrets["log_address"], st.secrets["log_id"]))
    syslog.addFilter(ContextFilter())
    log_format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
    formatter = logging.Formatter(log_format, datefmt='%b %d %H:%M:%S')
    syslog.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    get_logger = logging.getLogger(name)
    get_logger.addHandler(syslog)
    get_logger.propagate = False
    # logger.setLevel(logging.INFO)
    return get_logger


logger = getlogger(__name__)
logger.propagate = False
logger.setLevel(logging.INFO)
