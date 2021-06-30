import logging
import os
import threading

from .data_models.person_pkg import Friend, Person, PersonInfo, Sex

LOGGER = logging.getLogger("producer")


class Producer(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False

    def start(self) -> "Producer":
        super().start()
        return self

    def run(self):
        count = 0
        LOGGER.info(f"Start")
        with open(os.path.join("proto_dump", "a.pb"), "ab") as f:
            while not self.__is_shut_down.wait(10):
                count += 1
                person = Person(info=PersonInfo(age=count, sex=Sex.M, height=160),
                                friends=[Friend(friendship_duration=365, shared_hobbies=[f"{count}", "bb", "cc"])])
                b = bytes(person)
                LOGGER.info(f"Write {count} {len(b)}")
                f.write(b)
                f.flush()
        LOGGER.info(f"End")

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
