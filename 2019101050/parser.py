import pickle
import string
import xml.sax
from typing import Optional
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import sys

nltk.download('stopwords')
stopword = stopwords.words('english')
snowball_stemmer = SnowballStemmer('english')
regex = re.compile(r'(\d+|\s+|=|\|)')
# import unicodedata
# import json

all_tokens = set()


class Page:
    def __init__(self, doc_no):
        self.doc_no: int = doc_no
        self.title: [str] = []
        self.body: [str] = []

    def __str__(self):
        print("----Doc---")
        print("Doc no", self.doc_no)
        print("Titl", ' '.join(self.title))
        # print("Info", self.infobox)
        # print("Cat", self.category)
        # print("Links", self.links)
        # print("Refs", self.references)
        print("----End Doc---")
        return ""


TAG_MEDIA_WIKI = "mediawiki"
TAG_PAGE = "page"
TAG_ID = "id"
TAG_TEXT = "text"
TAG_TITLE = "title"


def shortAndAscii(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


totalToken = 0
stemmed_dict = {}
word_set = {}

indexed_dict = {}
doc_id = 0


# id_to_title = {}


def stem(token):
    if token in stemmed_dict:
        return stemmed_dict[token]
    else:
        temp = snowball_stemmer.stem(token)
        stemmed_dict[token] = temp
        return temp


def tokenizer(txt, count=False):
    global regex
    txt = txt.lower()
    punc_list = '\n\r\!"#$&*+,-./;?@\^_~)({}[]:|=<>'
    # punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
    # txt = txt.translate(str.maketrans('', '', string.punctuation))

    t = str.maketrans(dict.fromkeys(punc_list, " "))
    txt = txt.translate(t)
    t = str.maketrans(dict.fromkeys("`'", ""))
    txt = txt.translate(t)
    # print("Text", txt)
    tokens = [token for token in txt.split()]
    # print("Tokens", tokens)

    if count and len(tokens):
        all_tokens.update(tokens)
        global totalToken
        totalToken += len(tokens)
    tokens = [stem(token) for token in tokens if
              token not in word_set and token.isalnum()]
    return tokens


def addTokensToIndex(tokens, pos, idx):
    global indexed_dict
    for key in tokens:
        # key = strip_accents(unkey)
        if not shortAndAscii(key) or not key.isalnum():
            continue
        if key not in indexed_dict:
            indexed_dict[key] = [[], [], [], [], [], []]
        if not indexed_dict[key][pos] or indexed_dict[key][pos][-1] != idx:
            indexed_dict[key][pos].append(idx)


def getInfobox(text):
    string = ""
    regex = re.compile('{{ ?Infobox ', re.I)
    segs = regex.split(text)[1:]

    if len(segs):
        split = re.split('}}', segs[-1])
        for j in split:
            if '{{' not in j:
                segs[-1] = j
                break

        string = '\n'.join(segs)

    return string


START_LINK = "startoflink"


# title: 0, info: 1, body: 2, cat: 3, refs: 4, links: 5

class WikiParser(xml.sax.handler.ContentHandler):
    def __init__(self):
        super().__init__()
        self.CurrentData = ""
        self.currentPage: Optional[Page] = None

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        global doc_id
        if tag == TAG_PAGE:
            self.currentPage = Page(doc_id)
            doc_id += 1

    def endElement(self, tag):
        if tag != TAG_PAGE:
            return
        # global id_to_title, totalToken

        # id_to_title[self.currentPage.doc_no] = self.currentPage.title
        # print(self.currentPage)
        if self.currentPage.doc_no % 1000 == 0:
            print(self.currentPage.doc_no, file=sys.stderr)
        body = ' '.join(self.currentPage.body)

        body = body.replace("==External links==", START_LINK)

        categories_str = re.findall('(?<=\[\[Category:)(.*?)(?=\]\])', body)
        ref_type_1 = []
        # print("ref type 1 ", ref_type_1)
        ref_type_3 = re.findall(r'<ref(.+?)>', body)
        lis = re.split(r"==References==|== References ==|== references ==|==references==", body, 1)
        if len(lis) > 1:
            ref_type_1 = [re.split(r"==|<|\[\[", lis[1])[0]]
        # ref_type_3 = re.findall(r'&lt;ref name=(.+?)&gt;', body)
        # ref_type_3 = re.findall(r'&lt;ref name=&quot;(.+?)&quot;', body)
        # print(self.currentPage)
        # print(ref_type_1)
        infobox = getInfobox(body)
        # print("Infobox", infobox)
        # print("Ref type1", ref_type_1)
        # print("Ref type3", ref_type_3)
        all_refs = ref_type_3 + ref_type_1
        # print("References", all_refs)
        # print("Categories", categories_str)
        category_tokens = []

        for str_itr in categories_str:
            all_tok = tokenizer(str_itr)
            category_tokens.extend(all_tok)

        refer_tokens = []
        for str_itr in all_refs:
            refer_tokens.extend(tokenizer(str_itr))

        tokens = tokenizer(body, count=True)
        # print("Tokens", tokens)
        body_flag = True
        link_flag = False

        # print(tokens)
        link_tokens = []
        body_tokens = []
        for token in tokens:
            if token == START_LINK:
                link_flag = True
                body_flag = False
                continue
            if body_flag:
                body_tokens.append(token)
            elif link_flag:
                # category section after links
                # TODO can be a false positive
                if token == 'categori':
                    break
                link_tokens.append(token)

        # print(link_tokens)
        idx = self.currentPage.doc_no
        title = ' '.join(self.currentPage.title)
        title_tokens = tokenizer(title, count=True)
        info_tokens = tokenizer(infobox)
        addTokensToIndex(title_tokens, 0, idx)
        addTokensToIndex(info_tokens, 1, idx)
        addTokensToIndex(body_tokens, 2, idx)
        addTokensToIndex(category_tokens, 3, idx)
        addTokensToIndex(refer_tokens, 4, idx)
        addTokensToIndex(link_tokens, 5, idx)

    def characters(self, content):
        if self.CurrentData == TAG_TEXT:
            self.currentPage.body.append(content)
        elif self.CurrentData == TAG_TITLE:
            self.currentPage.title.append(content)


def main():
    dump_location, output_folder, stats_file = sys.argv[1], sys.argv[2], sys.argv[3]
    print(dump_location, output_folder, stats_file)
    for word in stopword:
        word_set[word] = None
    handler = WikiParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(dump_location)
    print("writing index file")
    if output_folder[-1] == '/':
        output_folder = output_folder[:-1]
    pickle_out = open(f"{output_folder}/index.pkl", "wb+")
    pickle.dump(indexed_dict, pickle_out)
    # pickle_out = open(f"{output_folder}/id_to_title.pickle", "wb+")
    # pickle.dump(id_to_title, pickle_out)
    with open(stats_file, "w+") as text_file:
        text_file.write(f"{len(all_tokens)}\n{len(indexed_dict)}")
    # with open("keys.txt", "w+") as text_file:
    #     json.dump(list(sorted(indexed_dict.keys())), text_file)


if __name__ == "__main__":
    main()
