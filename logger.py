import logging
from colorlog import ColoredFormatter
import os
import datetime
import zoneinfo


base_dir = os.path.abspath(os.path.dirname(__file__))
now_tz = zoneinfo.ZoneInfo("Asia/Taipei")


class CreateLogger:
    def __init__(self):
        super().__init__()
        self.c_logger = self.color_logger()
        self.a_logger = self.anonymous_logger()
        logging.addLevelName(25, "ANONYMOUS")

    @staticmethod
    def color_logger():
        formatter = ColoredFormatter(
            fmt="%(white)s[%(asctime)s] %(log_color)s%(levelname)-10s%(reset)s %(blue)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "ANONYMOUS": "purple",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red",
            },
        )

        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        log_path = os.path.join(base_dir, "logs",
                                f"logs {datetime.datetime.now(tz=now_tz).strftime('%Y.%m.%d %H.%M.%S')}.log")
        with open(log_path, "w"):
            pass
        f_formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-10s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        f_handler = logging.FileHandler(log_path, encoding="utf-8")
        f_handler.setFormatter(f_formatter)
        logger.addHandler(f_handler)
        logger.setLevel(logging.DEBUG)

        return logger

    @staticmethod
    def anonymous_logger():
        formatter = logging.Formatter(
            fmt="[%(asctime)s] %(levelname)-8s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S")
        logger = logging.getLogger("anonymous_logger")
        handler = logging.FileHandler("anonymous.log", encoding="utf-8")
        handler.setLevel(25)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def debug(self, message: str):
        self.c_logger.debug(message)

    def info(self, message: str):
        self.c_logger.info(message)

    def warning(self, message: str):
        self.c_logger.warning(message)

    def error(self, message: str):
        self.c_logger.error(message)

    def critical(self, message: str):
        self.c_logger.critical(message)

    def anonymous(self, message: str):
        self.c_logger.log(25, message)
        self.a_logger.log(25, message)
