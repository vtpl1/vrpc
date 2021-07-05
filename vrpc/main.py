import argparse
import codecs
import logging
import logging.config
import os
import shutil
import signal
import threading

import ruamel.yaml

from .consumer import Consumer
from .producer import Producer
from .utils import get_generated_engines_folder, get_session_folder


def setup_logging(default_path="logging.yaml"):
    """Setup logging configuration"""
    path = get_session_folder() + default_path
    if not os.path.exists(path):
        shutil.copy(os.path.join(os.path.dirname(__file__), "logging.yaml"), path)

    with open(path, "rt") as f:
        config = ruamel.yaml.safe_load(f.read())
    logging.config.dictConfig(config)

    # logging.basicConfig(level=default_level)


def read(rel_path):
    here = os.path.abspath(os.path.dirname(__file__))
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, rel_path), "r") as fp:
        return fp.read()


def get_version():
    return read("VERSION")


is_shutdown = threading.Event()

LOGGER = logging.getLogger(__name__)


def stop_handler(*args):
    # del signal_received, frame
    LOGGER.info("")
    LOGGER.info("=============================================")
    LOGGER.info("Bradcasting global shutdown from stop_handler")
    LOGGER.info("=============================================")
    # zope.event.notify(shutdown_event.ShutdownEvent("KeyboardInterrupt received"))
    global is_shutdown
    is_shutdown.set()


def init_argparser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Deeper look engine")
    return parser


def main():
    signal.signal(signal.SIGINT, stop_handler)
    signal.signal(signal.SIGTERM, stop_handler)
    setup_logging()
    LOGGER.info("=============================================")
    LOGGER.info("        Started  {} {}              ".format(__name__, get_version()))
    LOGGER.info("=============================================")
    try:
        global is_shutdown
        parser = init_argparser()
        args = parser.parse_args()
        o_consumer = Consumer(12)
        o_consumer.start()

        o_producer1 = Producer(0, 12)
        o_producer1.start()
        o_producer2 = Producer(1, 12)
        o_producer2.start()

        while not is_shutdown.wait(10.0):
            continue
    except Exception as e:
        LOGGER.exception(f"Startup issue: {e}")

    o_producer1.stop()
    o_producer2.stop()
    o_consumer.stop()
    LOGGER.info("=============================================")
    LOGGER.info("    Shutdown complete {} {}               ".format(__name__, get_version()))
    LOGGER.info("=============================================")
    return 0
