# encoding=utf8

import pickle
from collections import OrderedDict

import tensorflow as tf
import numpy as np

from ner.data_utils import BatchManager
from ner.loader import load_sentences, tag_mapping, prepare_dataset
from ner.model import Model
from ner.utils import test_ner, make_path, load_config, save_config
from ner.utils import get_logger, print_config, create_model, save_model, clean
import os, time

project_dir = os.path.dirname(os.path.abspath(__file__))

# 以下是模型参数
flags = tf.app.flags
flags.DEFINE_boolean("clean", False, "clean train folder")
flags.DEFINE_boolean("train", False, "Wither train the model")
# 配置模型
flags.DEFINE_integer("train_epoch", 50, "train epoches")
flags.DEFINE_integer("batch_size", 32, "batch size")
flags.DEFINE_integer("seg_dim", 20, "Embedding size for segmentation, 0 if not used")
flags.DEFINE_integer("char_dim", 100, "Embedding size for characters")
flags.DEFINE_integer("lstm_dim", 100, "Num of hidden units in LSTM")
flags.DEFINE_string("tag_schema", "iob", "tagging schema iobes or iob")

# 配置训练
flags.DEFINE_float("clip", 5, "Gradient clip")
flags.DEFINE_float("dropout", 0.5, "Dropout rate")
flags.DEFINE_float("lr", 0.001, "Initial learning rate")
flags.DEFINE_string("optimizer", "adam", "Optimizer for training")
flags.DEFINE_boolean("zeros", False, "Wither replace digits with zero")
flags.DEFINE_boolean("lower", True, "Wither lower case")

flags.DEFINE_integer("max_seq_len", 64, "max sequence length for bert")
flags.DEFINE_integer("max_epoch", 100, "maximum training epochs")
flags.DEFINE_integer("steps_check", 100, "steps per checkpoint")
flags.DEFINE_string("ckpt_path", "%s/ckpt" % project_dir, "Path to save model")
flags.DEFINE_string("summary_path", "%s/summary" % project_dir, "Path to store summaries")
flags.DEFINE_string("log_file", "%s/log/train.log" % project_dir, "File for log")
flags.DEFINE_string("map_file", "%s/maps.pkl" % project_dir, "file for maps")
flags.DEFINE_string("vocab_file", "%s/vocab.json" % project_dir, "File for vocab")
flags.DEFINE_string("config_file", "%s/config_file" % project_dir, "File for config")
flags.DEFINE_string("script", "%s/conlleval" % project_dir, "evaluation script")
flags.DEFINE_string("result_path", "%s/result" % project_dir, "Path for results")
flags.DEFINE_string("train_file", os.path.join("%s/data" % project_dir, "time.train"), "Path for train data")
flags.DEFINE_string("dev_file", os.path.join("%s/data" % project_dir, "time.dev"), "Path for dev data")
flags.DEFINE_string("test_file", os.path.join("%s/data" % project_dir, "time.test"), "Path for test data")

FLAGS = tf.app.flags.FLAGS


# 配置模型
def config_model(tag_to_id):
    config = OrderedDict()
    config["num_tags"] = len(tag_to_id)
    config["lstm_dim"] = FLAGS.lstm_dim
    config["batch_size"] = FLAGS.batch_size
    config["train_epoch"] = FLAGS.train_epoch
    config['max_seq_len'] = FLAGS.max_seq_len

    config["clip"] = FLAGS.clip
    config["dropout_keep"] = 1.0 - FLAGS.dropout
    config["optimizer"] = FLAGS.optimizer
    config["lr"] = FLAGS.lr
    config["tag_schema"] = FLAGS.tag_schema
    config["zeros"] = FLAGS.zeros
    config["lower"] = FLAGS.lower
    return config


def evaluate(sess, model, name, data, id_to_tag, logger):
    # 模型评估
    logger.info("evaluate:{}".format(name))
    ner_results = model.evaluate(sess, data, id_to_tag)  # 得到模型预测的结果
    eval_lines = test_ner(ner_results, FLAGS.result_path)  # 评估结果
    for line in eval_lines:
        logger.info(line)  # 逐行打印评估结果
    f1 = float(eval_lines[1].strip().split()[-1])

    if name == "test":
        best_test_f1 = model.best_test_f1.eval()
        if f1 > best_test_f1:
            tf.assign(model.best_test_f1, f1).eval()
            logger.info("new best test f1 score:{:>.3f}".format(f1))
        return f1 > best_test_f1


def train():
    # 加载数据集
    train_sentences = load_sentences(FLAGS.train_file, FLAGS.lower, FLAGS.zeros)
    dev_sentences = load_sentences(FLAGS.dev_file, FLAGS.lower, FLAGS.zeros)
    test_sentences = load_sentences(FLAGS.test_file, FLAGS.lower, FLAGS.zeros)

    # 创建id和标签的映射文件
    if not os.path.isfile(FLAGS.map_file):
        # Create a dictionary and a mapping for tags
        _t, tag_to_id, id_to_tag = tag_mapping(train_sentences)
        with open(FLAGS.map_file, "wb") as f:
            pickle.dump([tag_to_id, id_to_tag], f)
    else:
        with open(FLAGS.map_file, "rb") as f:
            tag_to_id, id_to_tag = pickle.load(f)

    # 对数据进行处理，得到可用于模型训练的数据集
    train_data = prepare_dataset(
        train_sentences, FLAGS.max_seq_len, tag_to_id, FLAGS.lower
    )
    dev_data = prepare_dataset(
        dev_sentences, FLAGS.max_seq_len, tag_to_id, FLAGS.lower
    )
    test_data = prepare_dataset(
        test_sentences, FLAGS.max_seq_len, tag_to_id, FLAGS.lower
    )

    train_manager = BatchManager(train_data, FLAGS.batch_size)
    dev_manager = BatchManager(dev_data, FLAGS.batch_size)
    test_manager = BatchManager(test_data, FLAGS.batch_size)
    # 创建模型和log的文件夹，若不存在才创建
    make_path(FLAGS)
    if os.path.isfile(FLAGS.config_file):
        config = load_config(FLAGS.config_file)  # 加载配置文件
    else:
        config = config_model(tag_to_id)  # 从FLAG中获取配置文件
        save_config(config, FLAGS.config_file)
    make_path(FLAGS)

    # 设置log
    log_path = os.path.join("log", FLAGS.log_file)
    logger = get_logger(log_path)
    print_config(config, logger)

    # 设置GPU内存使用
    tf_config = tf.ConfigProto()
    tf_config.gpu_options.allow_growth = True

    steps_per_epoch = train_manager.len_data  # batches
    with tf.Session(config=tf_config) as sess:
        # 创建模型
        model = create_model(sess, Model, FLAGS.ckpt_path, config, logger)

        logger.info("start training")
        loss = []
        # 训练
        for i in range(FLAGS.train_epoch):
            time_pass = time.time()
            # 获取batch
            for batch in train_manager.iter_batch(shuffle=True):
                step, batch_loss = model.run_step(sess, True, batch)  # 训练

                loss.append(batch_loss)  # 收集损失loss
                if step % FLAGS.steps_check == 0:  # 这里都是log
                    iteration = step // steps_per_epoch + 1
                    logger.info("iteration:{},step:{}/{},loss:{:>0.4f}".format(
                        iteration, step % steps_per_epoch, steps_per_epoch, np.mean(loss)
                    ))
                    loss = []
            # # 评估模型正确率
            best = evaluate(sess, model, "dev", dev_manager, id_to_tag, logger)
            if best:  # 保存模型， 分数刷新最高分纪录时才会保存模型，最终保存模型数是5个（定义的）
                save_model(sess, model, FLAGS.ckpt_path, logger, global_steps=step)
            evaluate(sess, model, "test", test_manager, id_to_tag, logger)
            time_local = time.time()
            print('this is {}/{} times, training speed is about {:>0.1f}s/epoch'
                  .format(i + 1, FLAGS.train_epoch, time_local - time_pass))
            time.sleep(10)


def main(_):
    FLAGS.train = True
    FLAGS.clean = True
    clean(FLAGS)
    train()


if __name__ == "__main__":
    time1 = time.time()
    os.environ['CUDA_VISIBLE_DEVICES'] = '0'
    tf.app.run(main)
    time2 = time.time()
    dis = time2-time1
    print('''----------\n
            The total training cost {:>0.1f}secs, {:>0.2f}mins, {:>0.2f}hours.\n
            ----------\n'''.format(dis, dis/60, dis/3600))
