import pprint
import sys
from copy import deepcopy
from nltk.stem import SnowballStemmer

snowball_stemmer = SnowballStemmer('english')
lines = []
dic = {}


def stem(token):
    return snowball_stemmer.stem(token)


def process_query(query):
    global dic
    units = query.split()
    # print(units)
    tokens = []
    for unit in units:
        if len(unit) > 2 and unit[1] == ':':
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
            dic[segments[0]] = [[], [], [], [], [], []]
            for segment in segments[1:]:
                segment = segment.strip()
                doc_id_freq = segment.split(":")
                doc_id = int(doc_id_freq[0], base=16)
                freq = int(doc_id_freq[1])
                for idx in range(6):
                    if (1 & (freq >> idx)) == 1:
                        dic[segments[0]][idx].append(doc_id)
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
    print(query_string)
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
