import pickle
import xml.sax
from typing import Optional
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import unicodedata
import sys
import json


class Page:
    def __init__(self, doc_no):
        self.id = ""
        self.doc_no: int = doc_no
        self.title = ""
        self.infobox = ""
        self.category = ""
        self.links = ""
        self.references = ""
        self.body = ""

    def __str__(self):
        print("----Doc---")
        print("Id", self.id)
        print("Titl", self.title)
        print("Info", self.infobox)
        print("Cat", self.category)
        print("Links", self.links)
        print("Refs", self.references)
        print("----End Doc---")
        return ""


TAG_MEDIA_WIKI = "mediawiki"
TAG_PAGE = "page"
TAG_ID = "id"
TAG_TEXT = "text"
TAG_TITLE = "title"


def shortAndEnglish(s):
    try:
        s.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')


totalToken = 0
stemmed_dict = {}

nltk.download('stopwords')
stopword = stopwords.words('english')
snowball_stemmer = SnowballStemmer('english')
word_set = {}

indexed_dict = {}
doc_id = 0
id_to_title = {}


def stem(token):
    if token in stemmed_dict:
        return stemmed_dict[token]
    temp = snowball_stemmer.stem(token)
    stemmed_dict[token] = temp
    return temp


def clean(txt):
    txt = txt.lower()
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
    tokens = [token for token in regex.split(txt)]
    global totalToken
    totalToken += len(tokens)
    tokens = [stem(token) for token in tokens if
              token not in word_set and (token.isalnum() or token == '}}' or token == '{{infobox')]
    return tokens


def addTokensToIndex(tokens, pos):
    global doc_id, indexed_dict

    for unkey in tokens:
        key = strip_accents(unkey)
        if not shortAndEnglish(key) or not key.isalnum():
            continue
        if key not in indexed_dict:
            indexed_dict[key] = [[], [], [], [], [], []]
        if not indexed_dict[key][pos] or indexed_dict[key][pos][-1] != doc_id:
            indexed_dict[key][pos].append(doc_id)


# title: 0, infobox: 1, body: 2, categories: 3, references: 4, external_links: 5

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
        global id_to_title, totalToken
        info_tokens = []
        link_tokens = []
        body_tokens = []
        body_flag = True
        link_flag = False
        info_flag = False
        id_to_title[self.currentPage.doc_no] = self.currentPage.title
        if self.currentPage.doc_no % 1000 == 0:
            print(self.currentPage.doc_no)
        tokens = regtok(self.currentPage.body)
        categories_str = re.findall('(?<=\[\[category:)(.*?)(?=\]\])', self.currentPage.body)
        ref_type_1 = re.findall('(?<=\* \[\[)(.*?)(?=\])', self.currentPage.body)
        ref_type_2 = re.findall('(?<=\* \{\{)(.*?)(?=\}\})', self.currentPage.body)
        category_tokens = []
        title_tokens = regtok(self.currentPage.title)

        for stri in categories_str:
            all_tok = regtok(stri)
            category_tokens.extend(all_tok)

        refer_tokens = []
        for stri in ref_type_1:
            refer_tokens.extend(regtok(stri))

        for stri in ref_type_2:
            refer_tokens.extend(regtok(stri))

        for token in tokens:
            if token == '{{infobox':
                info_flag = True
                body_flag = False
                continue

            if token == 'externallink':
                link_flag = True
                body_flag = False
                continue

            if info_flag is False and link_flag is False:
                body_flag = True

            if info_flag is True:
                if token == '}}':
                    info_flag = False
                    continue
                info_tokens.append(token)

            elif body_flag is True:
                body_tokens.append(token)

            elif link_flag is True and info_flag is False:
                link_tokens.append(token)

        addTokensToIndex(title_tokens, 0)
        addTokensToIndex(info_tokens, 1)
        addTokensToIndex(body_tokens, 2)
        addTokensToIndex(category_tokens, 3)
        addTokensToIndex(refer_tokens, 4)
        addTokensToIndex(link_tokens, 5)

    def characters(self, content):
        if self.CurrentData == TAG_TEXT:
            self.currentPage.body += content
        elif self.CurrentData == TAG_TITLE:
            self.currentPage.title += content


def main():
    dump_location, output_folder, stats_file = sys.argv[1], sys.argv[2], sys.argv[3]
    print(dump_location, output_folder, stats_file)
    for word in stopword:
        word_set[word] = None
    handler = WikiParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(dump_location)
    print("writing pickle file")
    if output_folder[-1] == '/':
        output_folder = output_folder[:-1]
    pickle_out = open(f"{output_folder}/index.pkl", "wb+")
    pickle.dump(indexed_dict, pickle_out)
    pickle_out = open(f"{output_folder}/id_to_title.pickle", "wb")
    pickle.dump(id_to_title, pickle_out)
    with open(stats_file, "w+") as text_file:
        text_file.write(f"{totalToken}\n{len(indexed_dict)}")
    with open("keys.txt", "w+") as text_file:
        json.dump(list(sorted(indexed_dict.keys())), text_file)


if __name__ == "__main__":
    main()
