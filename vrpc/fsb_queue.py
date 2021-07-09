import logging
import os

from .fsb_queue_producer import FsbQueueProducer



class FsbQueue():
    def create_producer(queue_id: str, channel_id: str) -> FsbQueueProducer:
        return FsbQueueProducer(queue_id, channel_id)

    def create_consumer(queue_id: str) -> None:
        return None
