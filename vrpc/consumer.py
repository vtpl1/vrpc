import threading


class Consumer(threading.Thread):
    def __init__(self) -> None:
        super().__init__()
        self.__is_shut_down = threading.Event()
        self.__already_shutting_down = False

    def run(self):
        while not self.__is_shut_down.is_set():
            pass
        pass

    def stop(self):
        if self.__already_shutting_down:
            return
        self.__already_shutting_down = True
        self.__is_shut_down.set()
