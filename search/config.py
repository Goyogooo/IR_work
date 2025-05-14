# !/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import math
import os
import pickle
import pandas as pd

# 获取当前脚本文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义文件夹路径
path = os.path.join(current_dir, '../frequency')  # 定位到 frequency 文件夹
path2 = os.path.join(current_dir, '..')          # 定位到上一级目录
binary_path = os.path.join(current_dir, '../binary_files')  # 二进制文件存储位置


def load_binary_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Binary file not found: {file_path}")
    with open(file_path, 'rb') as f:
        return pickle.load(f)

# 加载二进制文件
advanced_search_index = load_binary_file(os.path.join(binary_path, 'index.pkl'))
inverted_index = load_binary_file(os.path.join(binary_path, 'inverted_index.pkl'))
word_frequency = load_binary_file(os.path.join(binary_path, 'word_frequency.pkl'))
word_set = load_binary_file(os.path.join(binary_path, 'word_set.pkl'))
idf = load_binary_file(os.path.join(binary_path, 'word_idf.pkl'))
tf = load_binary_file(os.path.join(binary_path, 'tf.pkl'))
tf_idf = load_binary_file(os.path.join(binary_path, 'tf-idf.pkl'))
url_title_df = load_binary_file(os.path.join(binary_path, 'title_url_desc.pkl'))
inverted_index_title_only = load_binary_file(os.path.join(binary_path, 'inverted_index_title_only.pkl'))
word_frequency_title_only = load_binary_file(os.path.join(binary_path, 'word_frequency_title_only.pkl'))
word_set_title_only = load_binary_file(os.path.join(binary_path, 'word_set_title_only.pkl'))
idf_title_only = load_binary_file(os.path.join(binary_path, 'word_idf_title_only.pkl'))
tf_title_only = load_binary_file(os.path.join(binary_path, 'tf_title_only.pkl'))
tf_idf_title_only = load_binary_file(os.path.join(binary_path, 'tf-idf_title_only.pkl'))
page_rank_df = load_binary_file(os.path.join(binary_path, 'page_rank.pkl'))
