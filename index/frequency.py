# !/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import math
import json
import pandas as pd

df = pd.read_csv("./index.csv", encoding='utf-8-sig')
df = df.set_index('url')
# 将nan替换为""
df = df.fillna("")

# 检查frequency目录是否存在
if not os.path.exists("./frequency"):
    os.mkdir("./frequency")

# 设置排除停用词
with open('./stopwords.txt', 'r', encoding='utf-8') as f:
    stopwords = f.read().splitlines()
    add_stopwords = ['要闻', '新闻', '新闻网','志愿','志愿服务','日记', '讯','...']
    # 合并list
    stopwords += add_stopwords


index = {}
for url, row in df.iterrows():
    index[url] = {}
    for word in row['title'].split(" "):
        if word not in stopwords:
            if word not in index[url]:
                index[url][word] = 1
            else:
                index[url][word] += 1
    for word in row['description'].split(" "):
        if word not in stopwords:
            if word not in index[url]:
                index[url][word] = 1
            else:
                index[url][word] += 1
    for word in row['content'].split(" "):
        if word not in stopwords:
            if word not in index[url]:
                index[url][word] = 1
            else:
                index[url][word] += 1
    for word in row['editor'].split(" "):
        if word not in stopwords:
            if word not in index[url]:
                index[url][word] = 1
            else:
                index[url][word] += 1
    if index[url].get('') != None:
        del index[url]['']

word_frequency = {}
for url, words in index.items():
    for word, frequency in words.items():
        if word not in word_frequency:
            word_frequency[word] = 1
        else:
            word_frequency[word] += 1

inverted_index = {}
for url, words in index.items():
    for word, frequency in words.items():
        if word not in inverted_index:
            inverted_index[word] = {}
            inverted_index[word][url] = frequency
        else:
            inverted_index[word][url] = frequency

word_idf = {}
for url, frequency_dict in index.items():
    for word, frequency in frequency_dict.items():
        word_idf[word] = math.log(len(index) / frequency)

tf = {}
for url, words in index.items():
    temp_dict = {}
    for word, frequency in words.items():
        if word not in temp_dict:
            temp_dict[word] = 1
        else:
            temp_dict[word] += 1
    tf[url] = temp_dict

tf_idf = {}
for url, words in index.items():
    temp_dict = {}
    for word, frequency in words.items():
        temp_dict[word] = frequency * word_idf[word]
    tf_idf[url] = temp_dict

with open('./frequency/inverted_index.json', 'w', encoding='utf-8') as f:
    json.dump(inverted_index, f, ensure_ascii=False)

with open('./frequency/tf-idf.json', 'w', encoding='utf-8') as f:
    json.dump(tf_idf, f, ensure_ascii=False)

with open('./frequency/word_frequency.json', 'w', encoding='utf-8') as f:
    json.dump(word_frequency, f, ensure_ascii=False)

with open('./frequency/word_idf.json', 'w', encoding='utf-8') as f:
    json.dump(word_idf, f, ensure_ascii=False)

with open('./frequency/tf.json', 'w', encoding='utf-8') as f:
    json.dump(tf, f, ensure_ascii=False)

index = {}
for url, row in df.iterrows():
    index[url] = {}
    for word in row['title'].split(" "):
        if word not in stopwords:
            if word not in index[url]:
                index[url][word] = 1
            else:
                index[url][word] += 1

word_frequency = {}
for url, words in index.items():
    for word, frequency in words.items():
        if word not in word_frequency:
            word_frequency[word] = 1
        else:
            word_frequency[word] += 1

inverted_index = {}
for url, words in index.items():
    for word, frequency in words.items():
        if word not in stopwords:
            if word not in inverted_index:
                inverted_index[word] = {}
                inverted_index[word][url] = frequency
            else:
                inverted_index[word][url] = frequency

word_idf = {}
for url, frequency_dict in index.items():
    for word, frequency in frequency_dict.items():
        word_idf[word] = math.log(len(index) / frequency)

tf = {}
for url, words in index.items():
    temp_dict = {}
    for word, frequency in words.items():
        if word not in temp_dict:
            temp_dict[word] = 1
        else:
            temp_dict[word] += 1
    tf[url] = temp_dict

tf_idf = {}
for url, words in index.items():
    temp_dict = {}
    for word, frequency in words.items():
        temp_dict[word] = frequency * word_idf[word]
    tf_idf[url] = temp_dict

with open('./frequency/inverted_index_title_only.json', 'w', encoding='utf-8') as f:
    json.dump(inverted_index, f, ensure_ascii=False)

with open('./frequency/tf-idf_title_only.json', 'w', encoding='utf-8') as f:
    json.dump(tf_idf, f, ensure_ascii=False)

with open('./frequency/word_frequency_title_only.json', 'w', encoding='utf-8') as f:
    json.dump(word_frequency, f, ensure_ascii=False)

with open('./frequency/word_idf_title_only.json', 'w', encoding='utf-8') as f:
    json.dump(word_idf, f, ensure_ascii=False)

with open('./frequency/tf_title_only.json', 'w', encoding='utf-8') as f:
    json.dump(tf, f, ensure_ascii=False)
