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


class IndexItems(Enum):
    FREQ_ALL, FREQ_TITLE, FREQ_BODY, FREQ_REFS, FREQ_LINK, FREQ_CAT, FREQ_INFO, TOTAL_INDEX_TIMES = range(8)


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
        global totalToken
        global doc_id
        global indexed_dict
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
            totalToken += 1
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

        for unkey in refer_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][4] += 1
            if not indexed_dict[key][4] or indexed_dict[key][4][-1][0] != doc_id:
                indexed_dict[key][4].append([doc_id, 1])
            else:
                indexed_dict[key][4][-1][1] += 1

        for unkey in category_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][3] += 1
            if not indexed_dict[key][3] or indexed_dict[key][3][-1][0] != doc_id:
                indexed_dict[key][3].append([doc_id, 1])
            else:
                indexed_dict[key][3][-1][1] += 1

        for unkey in body_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][2] += 1
            if not indexed_dict[key][2] or indexed_dict[key][2][-1][0] != doc_id:
                indexed_dict[key][2].append([doc_id, 1])
            else:
                indexed_dict[key][2][-1][1] += 1

        for unkey in link_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][5] += 1
            if not indexed_dict[key][5] or indexed_dict[key][5][-1][0] != doc_id:
                indexed_dict[key][5].append([doc_id, 1])
            else:
                indexed_dict[key][5][-1][1] += 1

        for unkey in info_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][1] += 1
            if not indexed_dict[key][1] or indexed_dict[key][1][-1][0] != doc_id:
                indexed_dict[key][1].append([doc_id, 1])
            else:
                indexed_dict[key][1][-1][1] += 1

        for unkey in title_tokens:
            key = strip_accents(unkey)
            if not shortAndEnglish(key) or not key.isalnum():
                continue
            totalToken += 1
            if key not in indexed_dict:
                indexed_dict[key] = [[], [], [], [], [], [], [0, 0, 0, 0, 0, 0]]

            indexed_dict[key][6][0] += 1
            if not indexed_dict[key][0] or indexed_dict[key][0][-1][0] != doc_id:
                indexed_dict[key][0].append([doc_id, 1])
            else:
                indexed_dict[key][0][-1][1] += 1

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
    pickle_out = open("./output/index.pkl", "wb+")
    pickle.dump(indexed_dict, pickle_out)
    pickle_out = open("./output/id_to_title.pickle", "wb")
    pickle.dump(id_to_title, pickle_out)


if __name__ == "__main__":
    main()
