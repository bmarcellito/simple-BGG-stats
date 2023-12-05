import logging
import socket
from logging.handlers import SysLogHandler

import streamlit as st


def getlogger(name):
    class ContextFilter(logging.Filter):
        hostname = socket.gethostname()

        def filter(self, record):
            record.hostname = ContextFilter.hostname
            return True

    logging.basicConfig(level=logging.INFO)
    syslog = SysLogHandler(address=(st.secrets["log_address"], st.secrets["log_id"]))
    syslog.addFilter(ContextFilter())
    format = '%(asctime)s %(hostname)s YOUR_APP: %(message)s'
    formatter = logging.Formatter(format, datefmt='%b %d %H:%M:%S')
    syslog.setFormatter(formatter)
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    logger = logging.getLogger(name)
    logger.addHandler(syslog)
    logger.setLevel(logging.INFO)
    return logger, syslog
