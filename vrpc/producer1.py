import logging
import os
import struct
import threading

import cv2

from .data_models.data import FunctionTypes, FunctionTypesEnum
from .data_models.opencv import OcvMat
from .data_models.person_pkg import Friend, Person, PersonInfo, Sex
from .utils import get_folder

LOGGER = logging.getLogger("producer")


class Producer(threading.Thread):
    def __init__(self, channel_id=0, consumer_id=0) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False
        self.__consumer_id = consumer_id
        self.__channel_id = channel_id
        self.__file_count = 0
        self.__consumer_folder = f"{self.__consumer_id:05d}"

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        folder_name = get_folder(os.path.join("proto_dump", self.__consumer_folder))
        while not self.__is_shut_down.is_set():
            file_name = os.path.join(folder_name, f"{self.__channel_id:05d}_{self.__file_count:05d}.pb")
            with open(file_name, "ab") as f:
                while not self.__is_shut_down.wait(3):
                    image_name = os.path.join("images", "1.png")
                    mat = cv2.imread(image_name)
                    count += 1
                    person = Person(info=PersonInfo(age=count, sex=Sex.M, height=160),
                                    friends=[Friend(friendship_duration=365, shared_hobbies=[f"{count}", "bb", "cc"])])
                    function_types = FunctionTypes(function_types=FunctionTypesEnum.Data)
                    LOGGER.info(f"Write to {count} {f.tell()}")
                    b = bytes(function_types)
                    f.write(struct.pack("<i", len(b)))
                    f.write(b)
                    b = bytes(person)
                    f.write(struct.pack("<i", len(b)))
                    f.write(b)
                    (height, width, data_size) = mat.shape
                    ocvmat = OcvMat(rows=height, cols=width, mat_data_type=1, mat_data_size=data_size)
                    ocvmat.mat_data = bytes(mat.data)
                    b = bytes(ocvmat)
                    l = len(b)
                    print(f"Write size 1----------- {l}")
                    f.write(struct.pack("<i", l))
                    f.write(b)
                    f.flush()

                    if count % 100 == 0:
                        break
                LOGGER.info(f"Write End to {count} {f.tell()}")
                function_types = FunctionTypes(function_types=FunctionTypesEnum.Stop)
                b = bytes(function_types)
                l = len(b)
                f.write(struct.pack("<i", l))
                f.write(b)

                f.flush()
                LOGGER.info(f"Closing file {file_name} {f.tell()}")
            self.__file_count += 1

        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
