import glob
import logging
import ntpath
import os
import pathlib
import shutil
import struct
import sys
import time
from enum import Enum
from typing import Any, BinaryIO, Iterator, List, Optional, TextIO, Tuple

from .data_models.data import ObjectInfo
from .utils import get_folder, get_int, get_session_folder


def get_queue_base_folder() -> str:
    return get_session_folder()


class Mode(Enum):
    UNKNOWN = 0
    PRODUCER = 1
    CONSUMER = 2


LOGGER = logging.getLogger(__name__)

MAX_RECORDS = 100
_QUEUE_EXTENSION = ".fsbq"
_WRITE_SESSION_EXTENSION = ".fsws"
_READ_SESSION_EXTENSION = ".fsrs"
_FUNC_TYPE_DATA: int = 1
_FUNC_TYPE_EOF: int = 2


class _FsbQueueProducer:
    def __init__(self, queue_id: int, channel_id: int) -> None:
        self.__channel_id = channel_id
        self.__queue_id = queue_id
        self.__file_counter: int = 0
        self.__message_counter: int = 0
        self.__message_write_started: bool = False
        self.__offset: int = 0

        self.__q_folder = get_folder(os.path.join(get_queue_base_folder(), f"{self.__queue_id:05d}"))
        self.__file: Optional[BinaryIO] = None
        self.__producer_seek_file: Optional[BinaryIO] = None

        self.__find_last_file()
        self.__open()

    def __find_last_file(self):
        for file in glob.glob(os.path.join(self.__q_folder, f"{self.__channel_id:05d}_*{_QUEUE_EXTENSION}")):
            file_counter = get_int(ntpath.splitext(ntpath.basename(file))[0].split("_")[1])
            if file_counter > self.__file_counter:
                self.__file_counter = file_counter

    def __read_producer_seek_file(self) -> Tuple[int, int, int]:
        file_counter, message_counter, offset = 0, 0, 0
        if self.__producer_seek_file is None:
            session_file_name = os.path.join(self.__q_folder, f".{self.__channel_id:05d}{_WRITE_SESSION_EXTENSION}")
            try:
                if os.path.exists(session_file_name):
                    self.__producer_seek_file = open(session_file_name, "rb+")
                else:
                    self.__producer_seek_file = open(session_file_name, "wb+")
            except FileNotFoundError as e:
                LOGGER.fatal("Unexpected read error {e}")

        if self.__producer_seek_file is not None:
            try:
                file_counter, message_counter, offset = struct.unpack(
                    "<iQQ", self.__producer_seek_file.read(struct.calcsize("<iQQ")))
            except struct.error:
                pass
        return (file_counter, message_counter, offset)

    def __write_seek_file(self):
        if self.__producer_seek_file is None:
            session_file_name = os.path.join(self.__q_folder, f".{self.__channel_id:05d}{_WRITE_SESSION_EXTENSION}")
            try:
                if os.path.exists(session_file_name):
                    self.__producer_seek_file = open(session_file_name, "rb+")
                else:
                    self.__producer_seek_file = open(session_file_name, "wb")
            except FileNotFoundError as e:
                LOGGER.fatal("Unexpected read error {e}")

        if self.__producer_seek_file is not None:
            self.__offset = self.__file.tell()
            self.__producer_seek_file.seek(0)
            self.__producer_seek_file.write(
                struct.pack("<iQQ", self.__file_counter, self.__message_counter, self.__offset))
            self.__producer_seek_file.flush()

    def __open(self):

        file_counter, message_counter, offset = self.__read_producer_seek_file()
        if not self.__file_counter == file_counter:
            LOGGER.info(f"Resetting the write session {self.__file_counter} {file_counter}")

        self.__file_counter += 1
        self.__message_counter = message_counter
        self.__file_name = os.path.join(
            self.__q_folder,
            f"{self.__channel_id:05d}_{self.__file_counter:05d}{_QUEUE_EXTENSION}",
        )
        self.__file = open(self.__file_name, "wb")
        self.__write_seek_file()
        LOGGER.info(
            f"Opening file {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__message_counter}"
        )

    def put(self, item: ObjectInfo):
        if self.__message_write_started and self.__message_counter > 0 and self.__message_counter % MAX_RECORDS == 0:
            self.__mark_end()
            self.__close()
            self.__open()
        self.__message_counter += 1
        item.message_id = self.__message_counter
        b = bytes(item)
        l = len(b)
        if self.__file is not None:
            self.__message_write_started = True
            self.__file.write(struct.pack("<i", _FUNC_TYPE_DATA))
            self.__file.write(struct.pack("<i", l))
            self.__file.write(b)
            self.__file.flush()
        self.__write_seek_file()

    def __close(self):
        self.__file.close()
        self.__file = None
        self.__producer_seek_file.close()
        self.__producer_seek_file = None

    def __mark_end(self):
        self.__file.write(struct.pack("<i", _FUNC_TYPE_EOF))
        self.__file.flush()
        LOGGER.info(
            f"Marking end {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__message_counter}"
        )

    def stop(self):
        self.__mark_end()
        self.__close()


class _FsbQueueConsumer:
    def __init__(self, queue_id: int, channel_id: int) -> None:
        self.__channel_id = channel_id
        self.__queue_id = queue_id
        self.__file_counter: int = sys.maxsize
        self.__message_counter = 0
        self.__q_folder = os.path.join(get_queue_base_folder(), f"{self.__queue_id:05d}")
        self.__file: Optional[BinaryIO] = None
        self.__session_file_name = os.path.join(self.__q_folder, f".{self.__channel_id:05d}{_READ_SESSION_EXTENSION}")
        self.__producer_seek_file: Optional[BinaryIO] = None
        self.__consumer_seek_file: Optional[BinaryIO] = None

    def __find_first_file(self) -> bool:
        file_counter = sys.maxsize
        for file in glob.glob(os.path.join(self.__q_folder, f"{self.__channel_id:05d}_*{_QUEUE_EXTENSION}")):
            t = get_int(ntpath.splitext(ntpath.basename(file))[0].split("_")[1])
            if t < file_counter:
                file_counter = t
        if file_counter < sys.maxsize:
            self.__file_counter = file_counter
            return True
        return False

    def __delete(self):
        os.remove(self.__file_name)
        os.remove(self.__session_file_name)

    def __read_producer_seek_file(self) -> Tuple[int, int, int]:
        file_counter, message_counter, offset = 0, 0, 0
        if self.__producer_seek_file is None:
            session_file_name = os.path.join(self.__q_folder, f".{self.__channel_id:05d}{_WRITE_SESSION_EXTENSION}")
            try:
                self.__producer_seek_file = open(session_file_name, "rb")
            except FileNotFoundError as e:
                LOGGER.fatal("Unexpected read error {e}")

        if self.__producer_seek_file is not None:
            try:
                file_counter, message_counter, offset = struct.unpack(
                    "<iQQ", self.__producer_seek_file.read(struct.calcsize("<iQQ")))
            except struct.error:
                pass
        return (file_counter, message_counter, offset)

    def __open_seek_file(self):
        if self.__consumer_seek_file is None:
            try:
                if os.path.exists(self.__session_file_name):
                    self.__consumer_seek_file = open(self.__session_file_name, "rb+")
                else:
                    self.__consumer_seek_file = open(self.__session_file_name, "wb+")
            except FileNotFoundError as e:
                LOGGER.fatal("Unexpected read error {e}")

    def __read_seek_file(self) -> Tuple[int, int, int]:
        file_counter, message_counter, offset = 0, 0, 0
        self.__open_seek_file()
        if self.__consumer_seek_file is not None:
            self.__consumer_seek_file.seek(0)
            try:
                file_counter, message_counter, offset = struct.unpack(
                    "<iQQ", self.__consumer_seek_file.read(struct.calcsize("<iQQ")))
            except struct.error as e:
                pass
        return (file_counter, message_counter, offset)

    def __write_seek_file(self):
        self.__open_seek_file()
        if self.__consumer_seek_file is not None:
            self.__offset = self.__file.tell()
            self.__consumer_seek_file.seek(0)
            self.__consumer_seek_file.write(
                struct.pack("<iQQ", self.__file_counter, self.__message_counter, self.__offset))
            self.__consumer_seek_file.flush()

    def __open(self) -> bool:
        if not self.__find_first_file():
            return False
        self.__file_name = os.path.join(
            self.__q_folder,
            f"{self.__channel_id:05d}_{self.__file_counter:05d}{_QUEUE_EXTENSION}",
        )
        try:
            self.__file = open(self.__file_name, "rb")
        except FileNotFoundError as e:
            LOGGER.error(
                f"Read error very strange {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__message_counter} {e}"
            )
            return False

        LOGGER.info(
            f"Opening file {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__message_counter}"
        )

        return True

    def __close(self):
        if self.__file:
            self.__file.close()
            self.__file = None

        if self.__consumer_seek_file:
            self.__consumer_seek_file.close()
            self.__consumer_seek_file = None

        if self.__producer_seek_file:
            self.__producer_seek_file.close()
            self.__producer_seek_file = None

    def get(self) -> Optional[Tuple[int, ObjectInfo]]:
        if self.__file is None:
            self.__open()
        object_info: Optional[ObjectInfo] = None
        if self.__file is not None:
            _, message_counter, offset = self.__read_seek_file()
            self.__file.seek(offset)
            is_end_detected = False
            # LOGGER.info(f"Here 1 {self.__message_counter} {message_counter}")
            try:
                bytes_to_read = struct.calcsize("<i")
                function_type = struct.unpack("<i", self.__file.read(bytes_to_read))[0]
                if function_type == _FUNC_TYPE_DATA:
                    message_counter += 1
                    l = struct.unpack("<i", self.__file.read(struct.calcsize("<i")))[0]
                    if l == 0:
                        object_info = ObjectInfo()
                    elif l > 0:
                        b = self.__file.read(l)
                        object_info = ObjectInfo().parse(b)
                elif function_type == _FUNC_TYPE_EOF:
                    is_end_detected = True
            except struct.error:
                pass

            if self.__message_counter == message_counter:
                producer_file_counter, _, _ = self.__read_producer_seek_file()
                if producer_file_counter > self.__file_counter:
                    LOGGER.info(f"File counter difference found hence resetting {self.__file_counter} {producer_file_counter}")
                    is_end_detected = True
            else:
                self.__message_counter = message_counter
                self.__write_seek_file()

            if is_end_detected:
                self.__message_counter = 0
                self.__offset = 0
                self.__close()
                self.__delete()
        if object_info is None:
            time.sleep(0.1)
            return None
        return (self.__channel_id, object_info)

    def stop(self):
        self.__close()


class FsbQueue:
    def __init__(self, queue_id: int, channel_id: int = -1) -> None:
        # Required variable for common mode
        self.name = "FsbQueue"
        self.__queue_id: int = queue_id
        self.__channel_id: int = channel_id
        self.__q_folder: str = os.path.join(get_queue_base_folder(), f"{self.__queue_id:05d}")
        self.__mode: Mode = Mode.UNKNOWN
        self.__reset()
        # Required variables for consumer mode
        self.__list_fsb_queue_consumer: List[_FsbQueueConsumer] = [_FsbQueueConsumer(queue_id, channel_id), _FsbQueueConsumer(queue_id, 1)]
        self.__list_fsb_queue_consumer_iter: Iterator[_FsbQueueConsumer] = iter(self.__list_fsb_queue_consumer)

        # Required variables for producer mode
        self.__fsb_queue_producer: Optional[_FsbQueueProducer] = None

    def __reset(self):
        reset_file_name = os.path.join(self.__q_folder, "reset")
        if os.path.exists(reset_file_name):
            path = str(pathlib.Path(self.__q_folder).absolute())
            try:
                shutil.rmtree(path)    # remove dir and all contains
            except Exception as e:
                LOGGER.fatal(f"Queue reset exception {e}")
        pass

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
