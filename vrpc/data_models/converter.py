import numpy as np

from .data import OcvMat


def get_ocvmat_from_mat(mat) -> OcvMat:
    (height, width, data_size) = mat.shape
    ocvmat = OcvMat(rows=height, cols=width, mat_data_type=mat.dtype.num, mat_data_size=data_size)
    ocvmat.mat_data = bytes(mat.data)
    return ocvmat


def get_mat_from_ocvmat(ocvmat: OcvMat):
    print(f"mat_data_size {len(ocvmat.mat_data)}")
    mat = np.frombuffer(ocvmat.mat_data, dtype=np.uint8).reshape(ocvmat.rows, ocvmat.cols, ocvmat.mat_data_size)
    return mat
