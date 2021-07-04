import logging
import os
import struct
import threading
from vrpc.data_models.data import ObjectInfo
from vrpc.fsb_queue import FsbQueue

import cv2

from .utils import get_folder

LOGGER = logging.getLogger("producer")


class Producer(threading.Thread):
    def __init__(self, channel_id=0, queu_id=0) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False
        self.__fsb_q = FsbQueue(queu_id, channel_id=channel_id)

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        while not self.__is_shut_down.wait(0.3):
            item = ObjectInfo(message_id = count)
            self.__fsb_q.put(item)
            count += 1
        self.__fsb_q.stop()
        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True        
        self.__is_shut_down.set()
