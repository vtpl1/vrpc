from vrpc.data_models.data import ObjectInfo
#from vrpc.data_models.object_info_with_images_pb2 import ObjectInfo
import logging


def test_proto(caplog):
    caplog.set_level(logging.INFO)
    x = ObjectInfo()
    #x.message_id = 101
    x.spoof_tag = True
    b = bytes(x)    #.SerializeToString()
    l = len(b)
    y = ObjectInfo().parse(b)
    logging.info(f"{l} {b.hex()} {y}")