import logging
import os.path
from os import path, mkdir
import sys

if path.isdir('/home/pi/replay_video'):
    sys.path.append('/home/pi/replay_video')
import config


class LogGen:
    @staticmethod
    def loggen():
        if not os.path.isdir(path.join(config.BASE_DIR, config.VAR_DIR)):
            mkdir(path.join(config.BASE_DIR, config.VAR_DIR))

        logger = logging.getLogger()
        fhandler = logging.FileHandler(path.join(config.BASE_DIR, config.VAR_DIR, "replay_video.log"), mode='a')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fhandler.setFormatter(formatter)
        if logger.hasHandlers():
            logger.handlers.clear()
        logger.addHandler(fhandler)
        logger.setLevel(logging.INFO)
        return logger
