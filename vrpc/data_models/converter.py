from .data import OcvMat
import numpy as np

def get_ocvmat_from_mat(mat) -> OcvMat:
    (height, width, data_size) = mat.shape
    ocvmat = OcvMat(rows=height, cols=width, mat_data_type=1, mat_data_size=data_size)
    ocvmat.mat_data = bytes(mat.data)
    return ocvmat

def get_mat_from_ocvmat(ocvmat: OcvMat):
    mat = np.frombuffer(ocvmat.mat_data, dtype=np.uint8).reshape(ocvmat.rows, ocvmat.cols, ocvmat.mat_data_size)
    return mat