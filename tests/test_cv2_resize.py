import logging

from vrpc.data_models.data import ObjectInfo
import cv2
import numpy as np

def test_proto(caplog):
    caplog.set_level(logging.INFO)
    # path
    path = "/workspaces/vrpc/images/1.png"

    # Using cv2.imread() method
    img = cv2.imread(path)
    logging.info(f"img. {type(img.data)} img.shape {img.shape} {img.dtype.num} {img.dtype} {np.dtype(np.uint8).num}")
