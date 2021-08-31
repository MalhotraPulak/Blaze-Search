import pickle
import xml.sax
from typing import Optional
import nltk
from enum import Enum
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import unicodedata


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
BATCH_SIZE = 100


def shortAndEnglish(s):
    if len(s) > 20:
        return False
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


def addTokensToIndex(tokens, pos):
    global totalToken, doc_id, indexed_dict
    if pos == 0 or pos == 2:
        totalToken += len(tokens)
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
            # make sure this is copy by reference
            self.currentPage = Page(doc_id)
            doc_id += 1

    def endElement(self, tag):
        if tag != TAG_PAGE:
            return
        global id_to_title
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
            for tok in all_tok:
                category_tokens.append(tok)

        refer_tokens = []
        for stri in ref_type_1:
            all_tok = regtok(stri)
            for tok in all_tok:
                refer_tokens.append(tok)

        for stri in ref_type_2:
            all_tok = regtok(stri)
            for tok in all_tok:
                refer_tokens.append(tok)

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
    for word in stopword:
        word_set[word] = None
    handler = WikiParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse("wiki.xml")
    print("writing pickle file")
    new_index = {}
    for key, value in indexed_dict.items():
        new_index[key] = value[0:len(value) - 1]
    pickle_out = open("./output/index.pkl", "wb+")
    pickle.dump(new_index, pickle_out)
    pickle_out = open("./output/id_to_title.pickle", "wb")
    pickle.dump(id_to_title, pickle_out)


if __name__ == "__main__":
    main()
