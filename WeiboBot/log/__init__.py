import logging
import logging.handlers
import os
import sys
from logging import Logger


class Log(Logger):
    def __init__(self, name: str, level=logging.DEBUG, is_print=True, is_file=True):
        super(Log, self).__init__(name, level)
        if is_print:
            s_handler = logging.StreamHandler(sys.stdout)
            s_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s[%(funcName)s][:%(lineno)d] - %(message)s"))
            self.addHandler(s_handler)
        if is_file:
            log_path = f"{os.getcwd()}/Log/{name}/"
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            f_handler = logging.handlers.TimedRotatingFileHandler(log_path + f'/{name}.log', encoding='utf8')
            f_handler.suffix = ".%Y%m%d_%H"
            f_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(levelname)s - %(pathname)s[%(funcName)s][:%(lineno)d] - %(message)s"))
            self.addHandler(f_handler)
