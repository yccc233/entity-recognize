# -*- coding: utf-8 -*-

import pickle

import tensorflow as tf
from ner.utils import create_model, get_logger
from ner.model import Model
from ner.loader import input_from_line
from ner.train import FLAGS, load_config
import re
# from zhon.hanzi import punctuation


# 导入模型
config = load_config(FLAGS.config_file)
logger = get_logger(FLAGS.log_file)
# limit GPU memory
tf_config = tf.ConfigProto()
tf_config.gpu_options.allow_growth = False
with open(FLAGS.map_file, "rb") as f:
    tag_to_id, id_to_tag = pickle.load(f)
# 创建tensorflow 会话（session）
sess = tf.Session(config=tf_config)
# 初始化模型
model = create_model(sess, Model, FLAGS.ckpt_path, config, logger)


# 过滤杂项
def reprocess(textList):
    resList = []
    for text in textList:
        if len(text)<2:  # 文本长度较短的话，一般也是识别错误的
            continue
        resList.append(text)
    return resList


def outPutProcess(dataDict):
    # 为缓和数据少而导致的正确率不高的问题，这里对输出结果做过滤
    resDict = {}
    for key in dataDict:
        processedList = reprocess(dataDict[key])
        if not processedList:  # 如果结果为空，也过滤掉
            continue
        resDict[key] = processedList
    return resDict


def predict(text):
    text = text.replace('-', '_')
    # 使用训练好的模型，对文本进行命名实体识别，结果会返回json格式的数据
    res = model.evaluate_line(sess, input_from_line(text, FLAGS.max_seq_len, tag_to_id), id_to_tag)
    return outPutProcess(res['data'])  # 输出的结果，再次进行过滤处理，辅助提高正确率


if __name__ == '__main__':
    string = '新冠病毒最近在南京发生变异，感染源环境更加随意，好在打了疫苗后症状轻了许多。'
    result = predict(string)
    print(result)