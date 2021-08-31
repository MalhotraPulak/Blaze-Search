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
id_to_title = {}
doc_cnt = len(id_to_title.keys())
# Total number of docs encountered in the dump

doc_score = {}
dic = {}


def get_token_scores(word):
    if word in dic:
        return dic[word]
    return [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]


# title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5

def field_query(query, K):
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

    for token in tokens:
        scores[token] = get_token_scores(token)
        for field in range(6):
            for doc in scores[token][field]:
                temp = (1 + math.log(doc[1])) * math.log(doc_cnt / scores[token][6][field])
                if token in token_query[field]:
                    temp *= field_match_reward
                if doc[0] not in doc_score:
                    doc_score[doc[0]] = 0
                doc_score[doc[0]] += temp

    processed = 0
    for elem in (sorted(doc_score.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)):

        if elem[0] in id_to_title:
            print(str(elem[0]) + ", " + id_to_title[elem[0]].lower())
        else:
            print(str(elem[0])) + ", " + "_"

        processed += 1
        if processed == K:
            break


query_file = sys.argv[1]

file = open(query_file, "r+").read().split("\n")

for line in file:
    try:
        for word in stopword:
            word_set[word] = None
        # load id to title mapping
        print("Loading id to title mapping")
        file_id = open("/output/id_to_title.pickle", "rb")
        id_to_title = pickle.load(file_id)
        # load index in memory
        print("Loading index in memory")
        with open("output/index.pkl") as file:
            dic = pickle.load(file)
        print("Done loading index in memory")
        doc_score = {}
        start = time.time()
        K, query = line.split(", ")
        K = int(K)
        field_query(query, K)
        end = time.time()
        print(str(end - start) + ", " + str((end - start) / K))
        print()
    except:
        "Aww Snap. Some Error Occured. :/"
