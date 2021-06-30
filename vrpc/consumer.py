import logging
import os
import threading

LOGGER = logging.getLogger("consumer")
from .data_models.person_pkg import Friend, Person, PersonInfo, Sex


class Consumer(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False

    def start(self) -> "Consumer":
        super().start()
        return self

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        while not self.__is_shut_down.wait(1):
            try:
                with open(os.path.join("proto_dump", "a.pb"), "rb") as f:
                    while not self.__is_shut_down.wait(1):
                        count += 1
                        try:
                            b = f.read(25)
                            pos = f.tell()
                            person = Person().parse(b)
                            LOGGER.info(f"Read --- {count} {pos} {person.to_dict()}")
                        except Exception as e:
                            LOGGER.error(f"Read Exception {e}")
            except FileNotFoundError as e:
                LOGGER.error(f"Read error {e}")

        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
