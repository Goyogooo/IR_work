import os
import pickle
import json  # Import the json module
# 获取当前脚本文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义文件夹路径
path = os.path.join(current_dir, '../frequency')  # 定位到 frequency 文件夹

# 定义文件夹路径
# path = '../frequency'

# 读取词频数据
with open(os.path.join(path, 'word_frequency.json'), 'r', encoding='utf-8') as f:
    word_frequency = json.load(f)
    word_set = sorted(set(word_frequency.keys()))

with open(os.path.join(path, 'word_frequency_title_only.json'), 'r', encoding='utf-8') as f:
    word_frequency_title_only = json.load(f)
    word_set_title_only = sorted(set(word_frequency_title_only.keys()))

# 保存为二进制文件
def save_as_binary(data, binary_path):
    with open(binary_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved binary file: {binary_path}")

# 保存 word_set 和 word_set_title_only
save_as_binary(word_set, os.path.join(path, 'word_set.pkl'))
save_as_binary(word_set_title_only, os.path.join(path, 'word_set_title_only.pkl'))
