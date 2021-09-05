import pprint
import sys
from copy import deepcopy
from nltk.stem import SnowballStemmer

snowball_stemmer = SnowballStemmer('english')
lines = []
dic = {}


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


def process_query(query):
    global dic
    units = query.split()
    # print(units)
    tokens = []
    for unit in units:
        if len(unit) >= 3:
            if unit[1] == ':':
                unit = unit[2:]
        tokens.append(unit)
    # print(tokens)
    ans = {}
    for token in tokens:
        # title: 0, info: 1, body: 2, cat: 3, ref: 4, links: 5
        og = deepcopy(token)
        token = stem(token.lower())
        for line in lines:
            segments = line.split(';')
            if segments[0] != token:
                continue
            dic[token] = [[], [], [], [], [], []]
            for segment in segments[1:]:
                segment = segment.strip()
                doc_id_freq = segment.split(":")
                doc_id = int(doc_id_freq[0], base=16)
                freq_str = str(doc_id_freq[1]) + 'z'
                last = ''
                freq = 0
                print(doc_id, freq_str)
                for c in freq_str:
                    if c in list(field_map.keys()) + ['p', 'q']:
                        if c == 'p':
                            dic[token][2].append([doc_id, 1])
                        elif c == 'q':
                            dic[token][1].append([doc_id, 1])
                        if freq != 0 and last:
                            dic[token][field_map[last]].append([doc_id, freq])
                            freq = 0
                        last = c
                    else:
                        freq = freq * 10 + int(c) 
            break
        ans[og] = {}
        if token in dic:
            dic_token = dic[token]
        else:
            dic_token = [[], [], [], [], [], []]
        ans[og]["title"] = dic_token[0]
        ans[og]["body"] = dic_token[2]
        ans[og]["infobox"] = dic_token[1]
        ans[og]["categories"] = dic_token[3]
        ans[og]["references"] = dic_token[4]
        ans[og]["links"] = dic_token[5]
        for key, value in ans[og].items():
            if not value:
                ans[og][key] = ["No Doc Found"]
    pprint.pprint(ans, indent=1)


def main():
    global lines
    index_loc, query_string = sys.argv[1], sys.argv[2]
    # print(query_string)
    global dic
    try:
        if index_loc[-1] == '/':
            index_loc = index_loc[: -1]
        with open(f"{index_loc}/index.txt", "r") as file:
            lines = file.readlines()
        process_query(query_string)
        print()
    except Exception as e:
        print("Error", e)


if __name__ == "__main__":
    main()
