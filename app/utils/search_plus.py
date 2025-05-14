# !/usr/bin/env python
# -*- coding: utf-8 -*-


import re
import os
from search.config import advanced_search_index
import math
import time
from jieba import cut_for_search
from typing import List, Tuple
from search.config import *
import heapq
from flask import current_app

# 获取当前脚本文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 项目根目录（两级上层：从 routes/search_routes.py 到 project 根目录）
project_root = os.path.abspath(os.path.join(current_dir, "../../"))

# 定位 title_url_desc.csv 的路径
csv_path = os.path.join(project_root, "index.csv")
index = pd.read_csv(csv_path, encoding='utf-8-sig', index_col='url')
            
key_valid_number = 500  # 有效关键词数量


def wildcard_search(input_word: str):
    # 处理 * 和 ?，确保它们只匹配一个字符
    # 将 * 替换为 .*, 表示匹配任意多个字符
    # 将 ? 替换为 ., 表示匹配一个字符
    wildcard_pattern = re.escape(input_word).replace(r'\*', '.*').replace(r'\?', '.')
    
    # 使用 ^ 和 $ 确保从头到尾匹配
    wildcard_regex = re.compile(f"^{wildcard_pattern}$", re.IGNORECASE)
    
    return wildcard_regex

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



def main_func(
    input_word: str,
    history_words: List[str],
    is_title_only: bool = False,
    exact_phrases: List[str] = None,
    site_domain: str = None,
    enable_wildcard: bool = False)-> List[Tuple[str, float]]:
    
    current_app.logger.debug("Starting main function with input_word: %s, history_words: %s, is_title_only: %s", input_word, history_words, is_title_only)
   
    split_history = []
    for history_word in history_words:
        temp_split = list(cut_for_search(history_word))
        split_history.extend([word for word in temp_split if word.strip() and word not in split_history])

    # 判断搜索模式
    tf_dict = tf_title_only if is_title_only else tf
    idfs = idf_title_only if is_title_only else idf
    word_sets = word_set_title_only if is_title_only else word_set
    inverted_idx = inverted_index_title_only if is_title_only else inverted_index

    relevant_urls = set()

    # 判断是否启用通配符查询
    if enable_wildcard:
        current_app.logger.debug("Starting TONGPEI ")
    
        wildcard_regex = wildcard_search(input_word)
        for url, doc_data in index.iterrows():
            # combined_text = f"{doc_data['title']} {doc_data['description']} {doc_data['content']}"
            target_text = doc_data['title']
            match = wildcard_regex.fullmatch(target_text)
            if match:
                current_app.logger.debug("Wildcard matched content: %s in URL: %s", match.group(), url)
                relevant_urls.add(url)
    else:
        split_input = list(cut_for_search(input_word))
        split_input = [word for word in split_input if word.strip()]
        inverted_idx = inverted_index_title_only if is_title_only else inverted_index
        for word in split_input:
            if word in inverted_idx:
                relevant_urls.update(inverted_idx[word].keys())


    # 如果启用了短语查询，则生成短语匹配的正则表达式
    if not relevant_urls and exact_phrases:
        phrase_patterns = [re.compile(re.escape(phrase), re.IGNORECASE) for phrase in exact_phrases]
        for url in index.index:
            doc_data = index.loc[url]
            target_text = doc_data['title'] if is_title_only else f"{doc_data['title']} {doc_data['description']} {doc_data['content']}"
            if all(pattern.search(target_text) for pattern in phrase_patterns):
                relevant_urls.add(url)
    
    # 站内查询限制
    if not relevant_urls and site_domain:
        for url in index.index:
            if site_domain in url:
                relevant_urls.add(url)

    if not relevant_urls:
        current_app.logger.warning("No results found for query: %s", input_word)
        return []

    # 计算查询向量的 TF-IDF 和其向量长度
    tf_input = computeTF(word_sets, split_input)
    tfidf_input = computeTFIDF(tf_input, idfs)
    key_input = sorted(tfidf_input.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]
    len_key_input = length(key_input)

    if len_key_input == 0:
        raise KeyError("No valid input keywords to process.")

   
    results = []
    for url in relevant_urls:
        # 计算文档的 TF-IDF 和其向量长度
        doc_tfidf = computeTFIDF(tf_dict[url], idfs)
        doc_key_tfidf = sorted(doc_tfidf.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]
        len_doc = length(doc_key_tfidf)

        # 计算与查询的余弦相似度
        num = sum(tfidf_input.get(word, 0) * doc_tfidf.get(word, 0) for word, _ in key_input)
        cos_sim = round(num / (len_key_input * len_doc), 4) if len_doc > 0 else 0

        if cos_sim > 0:
            results.append((url, cos_sim))

    # 历史记录个性化推荐
    if len(history_words) > 0:
        tf_history = computeTF(word_sets, split_history)
        tfidf_history = computeTFIDF(tf_history, idfs)
        key_history = sorted(tfidf_history.items(), key=lambda d: d[1], reverse=True)[:key_valid_number]
        len_key_history = length(key_history)

        for i, (url, sim) in enumerate(results):
            doc_tfidf = computeTFIDF(tf_dict[url], idfs)
            num = sum(tfidf_history.get(word, 0) * doc_tfidf.get(word, 0) for word, _ in key_history)
            len_doc = length(sorted(doc_tfidf.items(), key=lambda d: d[1], reverse=True)[:key_valid_number])
            history_sim = round(num / (len_key_history * len_doc), 4) if len_doc > 0 else 0
            results[i] = (url, sim + history_sim / 10)

     # 获取相似度最高的N个文档
    top_results = heapq.nlargest(50, results, key=lambda x: x[1])  # 限制返回条数最多为50
    
    return top_results # 限制返回条数

