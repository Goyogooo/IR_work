# !/usr/bin/env python
# -*- coding: utf-8 -*-

import math
import time
from jieba import cut_for_search
from typing import List, Tuple
from search.config import *
import heapq
from flask import current_app

key_valid_number = 500  # 有效关键词数量


# 统计词项tj在文档Di中出现的次数，也就是词频。
def computeTF(word_set, split):
    tf = dict.fromkeys(word_set, 0)
    for word in split:
        if word in word_set:
            tf[word] += 1
    for word, cnt in tf.items():
        tf[word] = math.log10(cnt + 1)  # TF = log10(N + 1) 减少文本长度带来的影响
    return tf


# 计算逆文档频率IDF
def computeIDF(tf_list):
    idf_dict = dict.fromkeys(tf_list[0], 0)  # 词为key，初始值为0
    N = len(tf_list)  # 总文档数量
    for tf in tf_list:  # 遍历字典中每一篇文章
        for word, count in tf.items():  # 遍历当前文章的每一个词
            if count > 0:  # 当前遍历的词语在当前遍历到的文章中出现
                idf_dict[word] += 1  # 包含词项tj的文档的篇数df+1
    for word, Ni in idf_dict.items():  # 利用公式将df替换为逆文档频率idf
        idf_dict[word] = round(math.log10(N / Ni), 4)  # N,Ni均不会为0 IDF = log10(N / df_t)
    return idf_dict  # 返回逆文档频率IDF字典


# 计算tf-idf(term frequency–inverse document frequency)
def computeTFIDF(tf, idfs):  # tf词频,idf逆文档频率
    tfidf = {}
    for word, tfval in tf.items():
        tfidf[word] = tfval * idfs[word]
    return tfidf


def length(key_list):
    num = 0
    for i in range(len(key_list)):
        num = num + key_list[i][1] ** 2
    return round(math.sqrt(num), 2)


def main(input_word: str, history_words: List[str], is_title_only: bool = False) -> List[Tuple[str, float]]:
    
   
    current_app.logger.debug("Starting main function with input_word: %s, history_words: %s, is_title_only: %s", input_word, history_words, is_title_only)
    # 对输入的关键词进行分词
    start_time = time.time()  # 程序开始计时

    split_input = list(cut_for_search(input_word))
    split_input = [word for word in split_input if word.strip()]  # 去除空字符串和空格

    # 对历史记录进行分词
    split_history = []
    for history_word in history_words:
        temp_split = list(cut_for_search(history_word))
        split_history.extend([word for word in temp_split if word.strip() and word not in split_history])



    # 判断搜索模式，全文搜索或标题搜索
    if not is_title_only:
        tf_dict = tf
        idfs = idf
        word_sets = word_set
        inverted_idx = inverted_index
    else:
        tf_dict = tf_title_only
        idfs = idf_title_only
        word_sets = word_set_title_only
        inverted_idx = inverted_index_title_only
    
    # 从倒排索引中筛选包含关键词的文档
    relevant_urls = set()
    for word in split_input:
        if word in inverted_idx:
            relevant_urls.update(inverted_idx[word].keys())


    if not relevant_urls:
        return []

    # 计算查询的 TF-IDF 和其向量长度
    tf_input = computeTF(word_sets, split_input)
    tfidf_input = computeTFIDF(tf_input, idfs)
    key_input = sorted(tfidf_input.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]
    len_key_input = length(key_input)

    if len_key_input == 0:
        raise KeyError("No valid input keywords to process.")
    
    # 计算历史记录的 TF-IDF 和其向量长度(个性化查询)
    tf_history = computeTF(word_sets, split_history)  # 历史记录的tf
    tfidf_history = computeTFIDF(tf_history, idfs)  # 历史记录的tf-idf
    key_history = sorted(tfidf_history.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]  # 历史记录的前100个关键词
    len_key_history = length(key_history)

    # 对每个相关文档计算余弦相似度
    similarities = []
    for url in relevant_urls:
        doc_tfidf = computeTFIDF(tf_dict[url], idfs)
        doc_key_tfidf = sorted(doc_tfidf.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]

        # 计算与查询的相似度
        num = sum(tfidf_input.get(word, 0) * doc_tfidf.get(word, 0) for word, _ in key_input)
        len_doc = length(doc_key_tfidf)
        cos_sim = round(num / (len_key_input * len_doc), 4) if len_doc > 0 else 0

        if cos_sim > 0:
            similarities.append((url, cos_sim))

    # 如果有历史记录，计算历史相关性（个性化查询）
    if len(history_words) > 0:
        for i, (url, sim) in enumerate(similarities):
            doc_tfidf = computeTFIDF(tf_dict[url], idfs)
            num = sum(tfidf_history.get(word, 0) * doc_tfidf.get(word, 0) for word, _ in key_history)
            len_doc = length(sorted(doc_tfidf.items(), key=lambda d: d[1], reverse=True)[:key_valid_number])
            history_sim = round(num / (len_key_history * len_doc), 4) if len_doc > 0 else 0
            similarities[i] = (url, sim + history_sim / 10)

    # 获取相似度最高的N个文档
    top_n = 50
    top_results = heapq.nlargest(top_n, similarities, key=lambda x: x[1])

   
    print(f"Total execution time: {time.time() - start_time:.4f} seconds")  # 打印总时间
    return top_results


if __name__ == '__main__':
    # 调试本文件需要把工作目录改为项目根目录
    print(main('运动会', []))
    # print(main('运动会', ['光影']))
    # print(main('运动会', ['光影'], True))
