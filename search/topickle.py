import os
import json
import pandas as pd
import pickle

# 获取当前脚本文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 定义文件夹路径
path = os.path.join(current_dir, '../frequency')  # 定位到 frequency 文件夹
path2 = os.path.join(current_dir, '..')          # 定位到上一级目录

# 定义二进制文件保存函数
def save_as_binary(data, binary_path):
    with open(binary_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"Saved binary file: {binary_path}")

# 转换 JSON 文件为二进制
def convert_json_to_binary(json_path, binary_path):
    if not os.path.exists(json_path):
        print(f"JSON file not found: {json_path}")
        return
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    save_as_binary(data, binary_path)

# 转换 CSV 文件为二进制
def convert_csv_to_binary(csv_path, binary_path):
    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return
    data = pd.read_csv(csv_path, encoding='utf-8')
    save_as_binary(data, binary_path)

# 转换文件列表
def main():
    # Frequency 文件夹中的文件
    frequency_files = [
        ('inverted_index.json', 'inverted_index.pkl'),
        ('word_frequency.json', 'word_frequency.pkl'),
        ('word_idf.json', 'word_idf.pkl'),
        ('tf.json', 'tf.pkl'),
        ('tf-idf.json', 'tf-idf.pkl'),
        ('inverted_index_title_only.json', 'inverted_index_title_only.pkl'),
        ('word_frequency_title_only.json', 'word_frequency_title_only.pkl'),
        ('word_idf_title_only.json', 'word_idf_title_only.pkl'),
        ('tf_title_only.json', 'tf_title_only.pkl'),
        ('tf-idf_title_only.json', 'tf-idf_title_only.pkl'),
    ]

    # 转换 JSON 文件
    for json_file, binary_file in frequency_files:
        json_path = os.path.join(path, json_file)
        binary_path = os.path.join(path, binary_file)
        convert_json_to_binary(json_path, binary_path)

    # 上一级目录中的 CSV 文件
    csv_files = [
        ('index.csv', 'index.pkl'),
        ('title_url_desc.csv', 'title_url_desc.pkl'),
        ('page_rank.csv', 'page_rank.pkl'),
    ]

    # 转换 CSV 文件
    for csv_file, binary_file in csv_files:
        csv_path = os.path.join(path2, csv_file)
        binary_path = os.path.join(path2, binary_file)
        convert_csv_to_binary(csv_path, binary_path)

if __name__ == "__main__":
    main()
