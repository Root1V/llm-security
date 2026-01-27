import logging
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG

LOG_FORMAT = (
    "%(asctime)s | "
    "%(log_color)s%(levelname)-8s%(reset)s | "
    "%(bold)s%(name)s%(reset)s | "
    "%(message)s"
)

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "blue",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}

handler = logging.StreamHandler()
handler.setLevel(LOG_LEVEL)
handler.setFormatter(
    ColoredFormatter(
        LOG_FORMAT,
        log_colors=LOG_COLORS,
        datefmt="%Y-%m-%d %H:%M:%S,%f",
    )
)

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
root_logger.handlers.clear()  
root_logger.addHandler(handler)
