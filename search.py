import pprint
import time
import _pickle as pickle
import sys
import os
import math

import nltk
# nltk.download('punkt')
import re
import os
import shutil
import bz2
import lzma

from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

stemmed_dict = {}

import unicodedata


def isEN(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


def stem(token):
    if token in stemmed_dict:
        return stemmed_dict[token]
    temp = snowball_stemmer.stem(token)
    stemmed_dict[token] = temp
    return temp


# nltk.download('stopwords')
stopword = stopwords.words('english')
snowball_stemmer = SnowballStemmer('english')
word_set = {}

indexed_dict = {}
doc_id = 0

token_count = 0


def clean(txt):
    txt = txt.replace("\n", " ").replace("\r", " ")
    punc_list = '!"#$&*+,-./;?@\^_~)('
    t = str.maketrans(dict.fromkeys(punc_list, " "))
    txt = txt.translate(t)
    t = str.maketrans(dict.fromkeys("'`", ""))
    txt = txt.translate(t)

    return txt


def regtok(txt):
    txt = clean(txt)
    regex = re.compile(r'(\d+|\s+|=|}}|\|)')
    tokens = [stem(token) for token in regex.split(txt) if
              token not in word_set and (token.isalnum() or token == '}}' or token == '{{infobox')]
    return tokens


def stri(lst):
    N = len(lst)
    disp = min(N, 100)
    store = ""

    for i in range(disp):
        if i + 1 < disp:
            store = store + str(lst[i]) + ", "
        else:
            store = store + str(lst[i])

    if N > disp:
        store = store + ", ..."
    return store


scores = {}
# stores returned postings of all encountered tokens
# id_to_title = {}
# doc_cnt = len(id_to_title.keys())
# Total number of docs encountered in the dump

doc_score = {}
dic = {}


def get_token_scores(word):
    if word in dic:
        return dic[word]
    return [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]


# title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5

def field_query(query):
    # t:World Cup i:2019 c:Cricket
    units = query.split(" ")
    token_query = [[], [], [], [], [], []]
    normal_query = []

    tokens = []
    field_match_reward = 5

    flag = -1
    for unit in units:
        if len(unit) > 2 and unit[1] == ':':
            if unit[0] == 't':
                flag = 0
            if unit[0] == 'i':
                flag = 1
            if unit[0] == 'b':
                flag = 2
            if unit[0] == 'c':
                flag = 3
            if unit[0] == 'r':
                flag = 4
            if unit[0] == 'l':
                flag = 5

            unit = unit[2:]

        now = regtok(strip_accents(unit.lower()))
        all_tokens = [stem(word) for word in now if word not in word_set and isEN(word) == True]
        if flag == -1:
            normal_query += all_tokens
        else:
            token_query[flag] += all_tokens
        tokens += all_tokens
    print(tokens)
    ans = {}
    for token in tokens:
        # title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5
        ans[token] = {}
        dic_token = dic[token]
        ans[token]["title"] = dic_token[0]
        ans[token]["body"] = dic_token[5]
        ans[token]["infobox"] = dic_token[1]
        ans[token]["categories"] = dic_token[2]
        ans[token]["references"] = dic_token[3]
        ans[token]["links"] = dic_token[4]
    print(ans)


def main():
    query_string = sys.argv[1]
    print(query_string)
    global dic
    try:
        for word in stopword:
            word_set[word] = None
        with open("./output/index.pkl", "rb+") as file:
            dic = pickle.load(file)
        print("Done loading index in memory")
        field_query(query_string)
        print()
    except Exception as e:
        print(e)
        print("Aww Snap. Some Error Occured. :/")


if __name__ == "__main__":
    main()
