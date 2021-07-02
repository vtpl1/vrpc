import logging
import os
import struct
from enum import Enum
import glob
import ntpath
from typing import Any, BinaryIO, Iterator, List, Optional, TextIO, Tuple

from .data_models.data import FunctionTypesEnum, SeekInfo, FunctionTypes, ObjectInfo
from .utils import get_session_folder, get_folder, get_int


class Mode(Enum):
    UNKNOWN = 0
    PRODUCER = 1
    CONSUMER = 2


LOGGER = logging.getLogger(__name__)

MAX_RECORDS = 100


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
        function_types = FunctionTypes(function_types=FunctionTypesEnum.Data)
        b = bytes(function_types)
        self.__file.write(struct.pack("<i", len(b)))
        self.__file.write(b)
        item.record_id = self.__record_count
        LOGGER.info(f"Writing {item}")
        b = bytes(item)
        self.__file.write(struct.pack("<i", len(b)))
        self.__file.write(b)
        self.__file.flush()
        self.__record_count += 1

    def __close(self):
        self.__file.close()
        self.__file = None

    def __mark_end(self):
        function_types = FunctionTypes(function_types=FunctionTypesEnum.Data)
        b = bytes(function_types)
        self.__file.write(struct.pack("<i", len(b)))
        self.__file.write(b)
        self.__file.flush()
        LOGGER.info(
            f"Marking end {self.__file_name} for Q_id: {self.__queue_id} Ch_id: {self.__channel_id} file_counter: {self.__file_counter} record: {self.__record_count}"
        )

    def stop(self):
        self.__mark_end()
        self.__close()


class _FsbQueueConsumer:
    def __init__(self, channel_id) -> None:
        self.__channel_id = channel_id
        self.__file_name = ""
        self.__seek_file_name = ""
        self.__file = None
        self.__seek_file = None

    def get(self) -> Optional[ObjectInfo]:
        object_info: Optional[ObjectInfo] = None
        if self.__seek_file is None:
            return object_info
        if self.__file is None:
            return object_info

        self.__seek_file.seek(0)
        seek_info = SeekInfo().parse(self.__seek_file.read())
        self.__file.seek(seek_info.offset)
        l = struct.unpack("<i", self.__file.read(struct.calcsize("<i")))[0]
        if l > 0:
            function_types = FunctionTypes().parse(self.__file.read(l))
            if function_types.function_types == FunctionTypesEnum.Data:
                l = struct.unpack("<i", self.__file.read(struct.calcsize("<i")))[0]
                if l > 0:
                    object_info = ObjectInfo().parse(self.__file.read(l))
                    seek_info.offset = self.__file.tell()
                    self.__seek_file.seek(0)
                    self.__seek_file.write(bytes(seek_info))
                    self.__seek_file.flush()

            elif function_types.function_types == FunctionTypesEnum.Finish:
                self.__delete()
        return object_info

    def __delete(self):
        pass

    def __open_file(self):
        if self.__file is not None:
            self.__file.close()
        self.__file = None
        self.__file = open(self.__file_name, "rb")
        if self.__seek_file is not None:
            self.__seek_file.close()
        self.__seek_file = None
        self.__seek_file = open(self.__seek_file_name, "rb")


class FsbQueue:
    def __init__(self, queue_id: int, channel_id: int = -1) -> None:
        # Required variable for common mode
        self.name = "FsbQueue"
        self.__queue_id: int = queue_id
        self.__channel_id: int = channel_id
        self.__queue_folder: str = os.path.join(self.name, f"{self.__queue_id:05d}")
        self.__mode: Mode = Mode.UNKNOWN

        # Required variables for consumer mode
        self.__list_fsb_queue_consumer: List[_FsbQueueConsumer] = []
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
            self.__mode = Mode.PRODUCER
        if not self.__mode == Mode.PRODUCER:
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

    def __add_new_consumer_in_list(self):
        pass
