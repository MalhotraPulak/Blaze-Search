import pprint
import pickle
import sys
from copy import deepcopy
from nltk.stem import SnowballStemmer

snowball_stemmer = SnowballStemmer('english')


def stem(token):
    return snowball_stemmer.stem(token)


# title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5

def field_query(query):
    # t:World Cup i:2019 c:Cricket
    units = query.split(" ")
    print(units)
    tokens = []
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

        tokens.append(unit)
    print(tokens)
    ans = {}
    for token in tokens:
        # title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5
        og = deepcopy(token)
        token = stem(token.lower())
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
    pprint.pprint(ans)


def main():
    index_loc, query_string = sys.argv[1], sys.argv[2]
    print(query_string)
    global dic
    try:
        if index_loc[-1] == '/':
            index_loc = index_loc[: -1]
        with open(f"{index_loc}/index.pkl", "rb+") as file:
            dic = pickle.load(file)
        print("Done loading index in memory")
        field_query(query_string)
        print()
    except Exception as e:
        print("Error", e)


if __name__ == "__main__":
    main()
