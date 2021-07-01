import glob
import logging
import os
import struct
import threading

from .data_models.function_pkg import FunctionTypes, FunctionTypesEnum

LOGGER = logging.getLogger("consumer")
from .data_models.person_pkg import Friend, Person, PersonInfo, Sex
from .utils import get_folder


class Consumer(threading.Thread):
    def __init__(self, consumer_id=0) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False
        self.__consumer_id = consumer_id
        self.__consumer_folder = f"{self.__consumer_id:05d}"

    def start(self) -> "Consumer":
        super().start()
        return self

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        folder_name = get_folder(f"proto_dump/{self.__consumer_folder}")
        while not self.__is_shut_down.is_set():
            file_list = glob.glob(os.path.join(folder_name, "*.pb"))
            for file in file_list:
                try:
                    with open(file, "rb") as f:
                        while not self.__is_shut_down.wait(1):
                            count += 1
                            try:
                                LOGGER.info(f"Read from {f.tell()}")
                                l = struct.unpack("<i", f.read(struct.calcsize("<i")))[0]
                                if l > 0:
                                    function_types = FunctionTypes().parse(f.read(l))
                                    #LOGGER.info(f"function_types: {function_types} {f.tell()}")
                                    if function_types.function_types == FunctionTypesEnum.Data:
                                        l = struct.unpack_from("<i", f.read(struct.calcsize("<i")))[0]
                                        if l > 0:
                                            person = Person().parse(f.read(l))
                                            #LOGGER.info(f"Read --- {count} {f.tell()} {person.to_dict()}")
                                    elif function_types.function_types == FunctionTypesEnum.Stop:
                                        break
                            except struct.error:
                                LOGGER.error(f"Zero length data read")
                                pass
                            except Exception as e:
                                LOGGER.error(f"Read Exception {e} {type(e)}")
                    LOGGER.info(f"Deleting file {file}")
                    os.remove(file)
                except FileNotFoundError as e:
                    LOGGER.error(f"Read error {e}")

        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
