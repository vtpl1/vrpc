import logging
import os
import struct
from enum import Enum
import glob
import ntpath
from typing import Any, BinaryIO, Iterator, List, Optional, TextIO, Tuple
import sys

from .data_models.data import ObjectInfo
from .utils import get_folder_name, get_session_folder, get_folder, get_int, get_session_folder_name


class Mode(Enum):
    UNKNOWN = 0
    PRODUCER = 1
    CONSUMER = 2


LOGGER = logging.getLogger(__name__)

MAX_RECORDS = 100

_FUNC_TYPE_DATA: int = 1
_FUNC_TYPE_EOF: int = 2

class _FsbQueueProducer:
    def __init__(self, queue_id: int, channel_id: int) -> None:
        self.__channel_id = channel_id
        self.__queue_id = queue_id
        self.__file_counter: int = 0
        self.__record_count = 0
        self.__q_folder = get_folder(os.path.join(get_session_folder(), f"{self.__queue_id:05d}"))
        self.__find_last_file()
        self.__open()

    def __find_last_file(self):
        for file in glob.glob(os.path.join(self.__q_folder, f"{self.__channel_id:05d}_*.pb")):
            file_counter = get_int(ntpath.splitext(ntpath.basename(file))[0].split("_")[1])
            if file_counter > self.__file_counter:
                self.__file_counter = file_counter

    def __open(self):
        self.__file_counter += 1
        self.__file_name = os.path.join(self.__q_folder, f"{self.__channel_id:05d}_{self.__file_counter:05d}.pb")
        LOGGER.info(
            f"Opening file {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count}"
        )
        self.__file = open(self.__file_name, "wb")

    def put(self, item: ObjectInfo):
        if self.__record_count > 0 and self.__record_count % MAX_RECORDS == 0:
            self.__mark_end()
            self.__close()
            self.__open()
        item.message_id = self.__record_count + 1
        b = bytes(item)
        l = len(b)
        self.__file.write(struct.pack("<i", _FUNC_TYPE_DATA))
        self.__file.write(struct.pack("<i", l))
        self.__file.write(b)
        self.__file.flush()
        self.__record_count += 1

    def __close(self):
        self.__file.close()
        self.__file = None

    def __mark_end(self):
        self.__file.write(struct.pack("<i", _FUNC_TYPE_EOF))
        self.__file.flush()
        LOGGER.info(
            f"Marking end {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count}"
        )

    def stop(self):
        self.__mark_end()
        self.__close()


class _FsbQueueConsumer:
    def __init__(self, queue_id: int, channel_id: int) -> None:
        self.__channel_id = channel_id
        self.__queue_id = queue_id
        self.__file_counter: int = sys.maxsize
        self.__record_count = 0
        self.__q_folder = get_folder_name(os.path.join(get_session_folder_name(), f"{self.__queue_id:05d}"))
        self.__file: Optional[BinaryIO] = None
        self.__seek_file: Optional[BinaryIO] = None

    def __find_first_file(self) -> bool:
        file_counter = sys.maxsize
        for file in glob.glob(os.path.join(self.__q_folder, f"{self.__channel_id:05d}_*.pb")):
            t = get_int(ntpath.splitext(ntpath.basename(file))[0].split("_")[1])
            if t < file_counter:
                file_counter = t
        if file_counter < sys.maxsize:
            self.__file_counter = file_counter
            return True
        return False

    def __delete(self):
        os.remove(self.__file_name)
        os.remove(self.__seek_file_name)

    def __open(self) -> bool:
        if not self.__find_first_file():
            return False

        self.__file_name = os.path.join(self.__q_folder, f"{self.__channel_id:05d}_{self.__file_counter:05d}.pb")
        self.__seek_file_name = os.path.join(self.__q_folder, f".{self.__channel_id:05d}.session")
        try:
            self.__file = open(self.__file_name, "rb")
        except FileNotFoundError as e:
            LOGGER.error(
                f"Read error very strange {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count} {e}"
            )
            return False

        LOGGER.info(
            f"Opening file {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count}"
        )

        file_mode = "wb+"
        if os.path.exists(self.__seek_file_name):
            file_mode = "rb+"
        try:
            self.__seek_file = open(self.__seek_file_name, file_mode)
        except FileNotFoundError as e:
            LOGGER.error(f"Read error {e}")
            return False

        LOGGER.info(
            f"Opening seek file {self.__file_name} file mode {file_mode} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count}"
        )
        return True

    def __close(self):
        if self.__file:
            self.__file.close()
            self.__file = None

        if self.__seek_file:
            self.__seek_file.close()
            self.__seek_file = None

    def get(self) -> Optional[Tuple[int, ObjectInfo]]:
        if self.__file is None:
            if not self.__open():
                return None
        
        if self.__seek_file is None or self.__file is None:
            return None
        
        self.__seek_file.seek(0)
        offset = 0
        file_counter = self.__file_counter
        try:
            file_counter, offset = struct.unpack("<iQ", self.__seek_file.read(struct.calcsize("<iQ")))
        except struct.error:
            pass
        LOGGER.info(f"READ: {offset}")
        #self.__file.seek(offset)
        try:
            bytes_to_read = struct.calcsize("<i")
            function_type = struct.unpack("<i", self.__file.read(bytes_to_read))[0]
            if function_type == _FUNC_TYPE_DATA:
                l = struct.unpack("<i", self.__file.read(struct.calcsize("<i")))[0]
                if l == 0:
                    object_info = ObjectInfo()
                elif l > 0:
                    b = self.__file.read(l)
                    object_info = ObjectInfo().parse(b)
                    offset = self.__file.tell()
                    self.__seek_file.seek(0)                    
                    self.__seek_file.write(struct.pack("<iQ", file_counter, offset))
                    self.__seek_file.flush()
                    return (self.__channel_id, object_info)
            elif function_type == _FUNC_TYPE_EOF:
                self.__close()
                self.__delete()
        except struct.error:
            pass
        return None

    def stop(self):
        self.__close()


class FsbQueue:
    def __init__(self, queue_id: int, channel_id: int = -1) -> None:
        # Required variable for common mode
        self.name = "FsbQueue"
        self.__queue_id: int = queue_id
        self.__channel_id: int = channel_id
        self.__queue_folder: str = os.path.join(self.name, f"{self.__queue_id:05d}")
        self.__mode: Mode = Mode.UNKNOWN

        # Required variables for consumer mode
        self.__list_fsb_queue_consumer: List[_FsbQueueConsumer] = [_FsbQueueConsumer(queue_id, channel_id)]
        self.__list_fsb_queue_consumer_iter: Iterator[_FsbQueueConsumer] = iter(self.__list_fsb_queue_consumer)

        # Required variables for producer mode
        self.__fsb_queue_producer: Optional[_FsbQueueProducer] = None

    def put(self, item: ObjectInfo):
        if self.__mode == Mode.UNKNOWN:
            self.__mode = Mode.PRODUCER
        if not self.__mode == Mode.PRODUCER:
            raise RuntimeError(f"The {self.name} is in {self.__mode} mode")
        if self.__fsb_queue_producer is None:
            self.__fsb_queue_producer = _FsbQueueProducer(self.__queue_id, self.__channel_id)
        self.__fsb_queue_producer.put(item)

    def get(self) -> Optional[Tuple[int, ObjectInfo]]:
        if self.__mode == Mode.UNKNOWN:
            self.__mode = Mode.CONSUMER
        if not self.__mode == Mode.CONSUMER:
            raise RuntimeError(f"The {self.name} is in {self.__mode} mode")

        fsb_queue_consumer = None
        try:
            fsb_queue_consumer = next(self.__list_fsb_queue_consumer_iter)
        except (StopIteration, RuntimeError):
            self.__list_fsb_queue_consumer_iter = iter(self.__list_fsb_queue_consumer)
            self.__add_new_consumer_in_list()

        if fsb_queue_consumer is None:
            return None
        return fsb_queue_consumer.get()

    def stop(self) -> None:
        if self.__fsb_queue_producer:
            self.__fsb_queue_producer.stop()
        for fsb_queue_consumer in self.__list_fsb_queue_consumer:
            fsb_queue_consumer.stop()

    def __add_new_consumer_in_list(self):
        pass
