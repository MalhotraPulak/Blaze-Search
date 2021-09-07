import pprint
import sys
from copy import deepcopy
from nltk.stem import SnowballStemmer

snowball_stemmer = SnowballStemmer('english')
WEIGHTS = [5, 3, 1, 2, 1, 1]


def stem(token):
    return snowball_stemmer.stem(token)

field_map = {
        'z': 0, 
        'y':1, 
        'x':2, 
        'v':3, 
        'u':4, 
        't':5
};

dic = {}
TOTAL_DOCS = 22000000
import math

def process_word(word, field):
    print("searching", word)
    index_file_loc = f"./mergedIndex/{word[0]}.txt"
    file = open(index_file_loc, "r")
    lines = file.readlines()
    tokens = []
    for line in lines:
        tokens = line.split(';')
        if tokens[0] != word:
            continue 
        else:
            break

    docs = tokens[1:]
    idf = math.log10(TOTAL_DOCS/ len(docs))

    for segment in tokens[1:]:
        segment = segment.strip()
        doc_id_freq = segment.split(":")
        doc_id = int(doc_id_freq[0], base=16)
        freq_str = str(doc_id_freq[1]) + 'z'
        last = ''
        freq = 0
        if doc_id not in dic:
            dic[doc_id] = 0
        for c in freq_str:
            if c in list(field_map.keys()) + ['p', 'q']:
                if c == 'p':
                    dic[doc_id] += WEIGHTS[2] * (1 + math.log10(1)) * idf
                elif c == 'q':
                    dic[doc_id] += WEIGHTS[1] * (1 + math.log10(1)) * idf
                if freq != 0 and last:
                    dic[doc_id] += WEIGHTS[field_map[last]] * (1 + math.log10(freq)) * idf
                    freq = 0
                last = c
            else:
                freq = freq * 10 + int(c) 
  



def process_query(query):
    units = query.split()
    # TODO translate text to remove punctuation
    # print(units)
    for unit in units:
        field = -1
        if len(unit) >= 3 and unit[1] == ":":
            tok = unit[0]
            if tok == 't':
                field = 0
            elif tok == 'i':
                field = 1
            elif tok == 'b':
                field = 2
            elif tok == 'c':
                field = 3
            elif tok == 'r':
                field = 4
            elif tok == 'l':
                field = 5
            unit = unit[2:]
        process_word(stem(unit.lower()), field) 

    global dic
    ans = {k: v for k, v in sorted(dic.items(), key=lambda item: -item[1])}
    keys = list(ans.keys())
    print(keys[:10])
    # print(tokens)
    # ans = {}
    # for token in tokens:
    #     # title: 0, info: 1, body: 2, cat: 3, ref: 4, links: 5
    #     og = deepcopy(token)
    #     token = stem(token.lower())
    #     for line in lines:
    #         segments = line.split(';')
    #         if segments[0] != token:
    #             continue
    #         dic[token] = [[], [], [], [], [], []]
    #         for segment in segments[1:]:
    #             segment = segment.strip()
    #             doc_id_freq = segment.split(":")
    #             doc_id = int(doc_id_freq[0], base=16)
    #             freq_str = str(doc_id_freq[1]) + 'z'
    #             last = ''
    #             freq = 0
    #             print(doc_id, freq_str)
    #             for c in freq_str:
    #                 if c in list(field_map.keys()) + ['p', 'q']:
    #                     if c == 'p':
    #                         dic[token][2].append([doc_id, 1])
    #                     elif c == 'q':
    #                         dic[token][1].append([doc_id, 1])
    #                     if freq != 0 and last:
    #                         dic[token][field_map[last]].append([doc_id, freq])
    #                         freq = 0
    #                     last = c
    #                 else:
    #                     freq = freq * 10 + int(c) 
    #         break
    #     ans[og] = {}
    #     if token in dic:
    #         dic_token = dic[token]
    #     else:
    #         dic_token = [[], [], [], [], [], []]
    #     ans[og]["title"] = dic_token[0]
    #     ans[og]["body"] = dic_token[2]
    #     ans[og]["infobox"] = dic_token[1]
    #     ans[og]["categories"] = dic_token[3]
    #     ans[og]["references"] = dic_token[4]
    #     ans[og]["links"] = dic_token[5]
    #     for key, value in ans[og].items():
    #         if not value:
    #             ans[og][key] = ["No Doc Found"]
    # pprint.pprint(ans, indent=1)


def main():
    global lines
    query_string = sys.argv[1]
    # print(query_string)
    global dic
    try:
        process_query(query_string)
    except Exception as e:
        print("Error", e)


if __name__ == "__main__":
    main()
