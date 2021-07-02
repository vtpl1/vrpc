import glob
import logging
import os
import struct
import threading
from .fsb_queue import FsbQueue
import cv2
import numpy as np
from .utils import get_folder, get_session_folder

LOGGER = logging.getLogger("consumer")


class Consumer(threading.Thread):
    def __init__(self, queu_id=0) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False
        self.__fsb_q = FsbQueue(queu_id, 0)

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        while not self.__is_shut_down.wait(0.5):
            ret = self.__fsb_q.get()
            if ret is None:
                continue
            channel_id, item = ret
            LOGGER.info(f"{channel_id} {item}")
        self.__fsb_q.stop()
        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
