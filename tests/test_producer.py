import logging
from vrpc.fsb_queue import FsbQueue
def test_producer(caplog):
    caplog.set_level(logging.INFO)
    x = FsbQueue.create_producer("", "")

    logging.info(x)