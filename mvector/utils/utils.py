import distutils.util

import numpy as np
from tqdm import tqdm


class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict_to_object(dict_obj):
    if not isinstance(dict_obj, dict):
        return dict_obj
    inst = Dict()
    for k, v in dict_obj.items():
        inst[k] = dict_to_object(v)
    return inst


# 根据对角余弦值计算准确率和最优的阈值
def cal_accuracy_threshold(y_score, y_true):
    y_score = np.asarray(y_score)
    y_true = np.asarray(y_true)
    best_accuracy = 0
    best_threshold = 0
    for i in tqdm(range(0, 100)):
        threshold = i * 0.01
        y_test = (y_score >= threshold)
        acc = np.mean((y_test == y_true).astype(int))
        if acc > best_accuracy:
            best_accuracy = acc
            best_threshold = threshold

    return best_accuracy, best_threshold


# 根据对角余弦值计算准确率
def cal_accuracy(y_score, y_true, threshold=0.5):
    y_score = np.asarray(y_score)
    y_true = np.asarray(y_true)
    y_test = (y_score >= threshold)
    accuracy = np.mean((y_test == y_true).astype(int))
    return accuracy


# 计算对角余弦值
def cosin_metric(x1, x2):
    return np.dot(x1, x2) / (np.linalg.norm(x1) * np.linalg.norm(x2))
