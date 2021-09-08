import sys
from nltk.stem import SnowballStemmer
from nltk.corpus import stopwords
import nltk
nltk.download('stopwords')
stopword = stopwords.words('english')

snowball_stemmer = SnowballStemmer('english')

word_set = {}

def stem(token):
    return snowball_stemmer.stem(token)

# title: 0, info: 1, body: 2, cat: 3, ref: 4, links: 5

field_map = {
        'z': 0, 
        'y':1, 
        'x':2, 
        'v':3, 
        'u':4, 
        't':5
};
WEIGHTS = [5, 3, 1, 2, 1, 1]

dic = {}
TOTAL_DOCS = 22000000
import math

def process_word(word, field):
    print("searching", word, file=sys.stderr)
    index_file_loc = f"./scratch/pulak/mergedIndex3/{word[0:3]}.txt"
    try:
        file = open(index_file_loc, "r")
    except:
        return
    lines = file.readlines()
    print("done loading file in memory", file=sys.stderr)
    tokens = []
    for line in lines:
        tokens = line.split(';', maxsplit=1)
        if tokens[0] != word:
            continue 
        else:
            break
    
    if tokens[0] != word:
        return
    tokens = tokens[1].strip().split(';') 
    print("Found", word, file=sys.stderr)
    doc_list = tokens
    idf = math.log10(TOTAL_DOCS/ len(doc_list))
    print("Idf is", idf)
    field_names = list(field_map.keys()) + ['p', 'q'] 
    print(len(tokens))
    for segment in doc_list:
        doc_id_freq = segment.split(":")
        doc_id = int(doc_id_freq[0], base=16)
        freq_str = str(doc_id_freq[1]) + 'z'
        last = ''
        freq = 0
        score = 0
        for c in freq_str:
            if c in field_names:
                if c == 'p':
                    score += WEIGHTS[2] * idf
                elif c == 'q':
                    score += WEIGHTS[1] * idf
                if freq != 0 and last:
                    score += WEIGHTS[field_map[last]] * (1 + math.log10(freq)) * idf
                    freq = 0
                last = c
            else:
                freq = freq * 10 + int(c) 
        if score < 5:
            continue
        if doc_id not in dic:
            dic[doc_id] = score
        else:
            dic[doc_id] += score
        
    print("Done adding to global dic", len(dic))
  



def process_query(query):
    # units = query.split()
    txt = query.lower()
    punc_list = '\n\r\!"#$&*+,-./;?@\^_~)({}[]|=<>'
    # punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
    # txt = txt.translate(str.maketrans('', '', string.punctuation))
    t = str.maketrans(dict.fromkeys(punc_list, " "))
    txt = txt.translate(t)
    t = str.maketrans(dict.fromkeys("`'", ""))
    txt = txt.translate(t)
    # print("Text", txt)
    tokens = txt.split()
    # print("Tokens", tokens)

    tokens = [stem(token) for token in tokens if
              token not in word_set and token.isalnum()]
  

    print("Tokens are:", tokens)
    field = -1
    for unit in tokens:
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
    # print(list(ans.values())[:100])
    print(keys[:10])
    print()
    for doc_id in keys[:10]:
        title_no = int(doc_id) // 50000; 
        with open(f"titles/title{title_no}.txt", "r") as f:
            lines = f.readlines()
            line_no = (doc_id % 50000) * 2
            print(lines[line_no][:-1], "{:.2f}".format(dic[doc_id]))
    

def main():
    global lines
    query_string = sys.argv[1]
    # print(query_string)
    for word in stopword:
        word_set[word] = None

    global dic
    try:
        process_query(query_string)
    except Exception as e:
        print("Error", e)


if __name__ == "__main__":
    main()
