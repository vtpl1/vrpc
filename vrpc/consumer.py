import glob
import logging
import os
import struct
import threading

import cv2
import numpy as np

from .data_models.converter import get_mat_from_ocvmat
from .fsb_queue import FsbQueueConsumer
from .utils import get_folder, get_session_folder

LOGGER = logging.getLogger("consumer")


class Consumer(threading.Thread):
    def __init__(self, queu_id=0) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False
        self.__fsb_q = FsbQueueConsumer(queu_id)

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        while not self.__is_shut_down.is_set():
            ret = self.__fsb_q.get()
            if ret is None:
                continue
            channel_id, item = ret
            LOGGER.info(f"{channel_id} {item.message_id}")
            try:
                face_chip_cv_mat = get_mat_from_ocvmat(item.face_chip)
                extended_face_chip_cv_mat = get_mat_from_ocvmat(item.extended_face_chip)
            except Exception as e:
                pass
        self.__fsb_q.stop()
        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
