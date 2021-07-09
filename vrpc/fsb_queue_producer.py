import logging
import os
import pathlib
import shutil
from . import utils
from typing import Any, BinaryIO, Optional, Union

LOGGER = logging.getLogger(__name__)

class _FsbQueueProducer:
    def __init__(self, queue_id: str, channel_id: str) -> None:
        self.__queue_id: str = queue_id
        self.__channel_id: str = channel_id
        self.__file_counter: int = 0
        self.__file: Optional[BinaryIO] = None
        

class FsbQueueProducer():
    """
    File stream backed Queue
    """
    def __init__(self, queue_id: Union[int, str], channel_id: Union[int, str]) -> None:
        self.__queue_id: str = utils.get_str_id(queue_id)
        self.__channel_id: str = utils.get_str_id(channel_id)
        self.__q_folder: str = utils.get_q_folder(self.__queue_id)
        self.__check_and_reset()
        self.__fsb_queue_producer: _FsbQueueProducer = _FsbQueueProducer(self.__queue_id, self.__channel_id)

    def __check_and_reset(queue_id: str):
        reset_file_name = os.path.join(FsbQueueProducer.__get_q_folder(), "reset")
        if os.path.exists(reset_file_name):
            path = str(pathlib.Path(FsbQueueProducer.__get_q_folder()).absolute())
            try:
                LOGGER.info(f"FSBQ {queue_id} reset start")
                shutil.rmtree(path)    # remove dir and all contains
                LOGGER.info(f"FSBQ {queue_id} reset success")
            except Exception as e:
                LOGGER.fatal(f"FSBQ {queue_id} reset exception {e}")

    def put(self, item: Any):
        self.__fsb_queue_producer.put(item)

    def stop(self) -> None:
        self.__fsb_queue_producer.stop()