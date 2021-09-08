import xml.sax
from typing import List
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re
import sys

nltk.download("stopwords")
stopword = stopwords.words("english")
snowball_stemmer = SnowballStemmer("english")
regex = re.compile(r"(\d+|\s+|=|\|)")

# all_tokens = set()

mystopwords = [
    "www",
    "https",
    "http",
    "com",
    "ref",
    "reflist",
    "jpg",
    "descript",
    "redirect",
    "categori",
    "name",
    "refer",
    "title",
    "date",
    "imag",
    "author",
    "url",
    "use",
    "infobox",
    "site",
    "web",
    "also",
    "defaultsort",
    "use",
    "list",
    "org",
    "publish",
    "cite",
    "websit",
    "caption",
]

doc_mem = 0
chunk_no = 0


class Page:
    def __init__(self, doc_no):
        self.doc_no: int = doc_no
        self.title: List[str] = []
        self.body: List[str] = []

    def __str__(self):
        print("----Doc---")
        print("Doc no", self.doc_no)
        print("Titl", " ".join(self.title))
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
        s.encode(encoding="utf-8").decode("ascii")
    except UnicodeDecodeError:
        return False
    else:
        return True


totalToken = 0
stemmed_dict = {}
word_set = {}
output_folder = ""

indexed_dict = {}
doc_id = 0

DOC_IN_MEM = 100000
OUTPUT_DELTA = 5000

# id_to_title = {}


def stem(token):
    if token in stemmed_dict:
        return stemmed_dict[token]
    else:
        temp = snowball_stemmer.stem(token)
        stemmed_dict[token] = temp
        return temp


def validToken(token):
    # filter tokens to make index smaller
    # remove long tokens they are probably wrong
    # remove numbers which are of greater than 4 length
    # remove some more stopped tokens
    if len(token) > 15:
        return False
    if token in mystopwords:
        return False
    if token[0] in "0123456789" and len(token) > 4:
        return False
    if any(c.isalpha() for c in token) and any(c.isdigit() for c in token):
        return False
    return True


def tokenizer(txt):
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
    tokens = txt.split()
    # print("Tokens", tokens)

    tokens = [
        stem(token)
        for token in tokens
        if token not in word_set and token.isalnum()
    ]

    tokens = [token for token in tokens if validToken(token)]

    return tokens


def addTokensToIndex(tokens, pos, idx):
    global indexed_dict
    for key in tokens:
        # key = strip_accents(unkey)
        if not shortAndAscii(key) or not key.isalnum():
            continue
        if key not in indexed_dict:
            indexed_dict[key] = [[], [], [], [], [], []]
        # print("Befor", key, idx, indexed_dict[key][pos])
        if not indexed_dict[key][pos] or indexed_dict[key][pos][-1][0] != idx:
            indexed_dict[key][pos].append([idx, 1])
        elif indexed_dict[key][pos][-1][0] == idx:
            indexed_dict[key][pos][-1][1] += 1
            # print(indexed_dict[key][pos][-1])
        # print("After", key, idx, indexed_dict[key][pos])


def get_infobox(text):
    ind = [
        m.start()
        for m in re.finditer(
            r"{{Infobox|{{infobox|{{ Infobox| {{ infobox", text
        )
    ]
    ans = ""
    for i in ind:
        counter = 0
        end = -2
        for j in range(i, len(text) - 1):
            starting, ending = text[j : j + 2], text[j : j + 2]
            if starting == "}}":
                counter -= 1
            elif ending == "{{":
                counter += 1
            if counter == 0:
                end = j + 1
                break
        ans += text[i : end + 1]
    return ans


def dump_index():
    global output_folder, chunk_no, indexed_dict, doc_mem
    print("writing index file")
    # write the current index to memory
    out = open(f"{output_folder}/index{chunk_no}.txt", "w+")
    lines = []
    for k, v in sorted(indexed_dict.items()):

        all_docs = {}
        segments = []
        for field_id, ll in enumerate(v):
            for doc in ll:
                doc_id, term_freq = doc
                if doc_id not in all_docs:
                    all_docs[doc_id] = [0, 0, 0, 0, 0, 0]
                all_docs[doc_id][field_id] = term_freq

        for (doccc, freq) in all_docs.items():
            freq_str = ""
            for field_id, freq_field in enumerate(freq):
                if freq_field == 0:
                    continue
                else:
                    # if one freq in body just use one byte to store it
                    if field_id == 1 and freq_field == 1:
                        freq_str += "q"
                    elif field_id == 2 and freq_field == 1:
                        freq_str += "p"
                    else:
                        freq_str += field_map[field_id] + str(freq_field)
            segments.append(str(hex(doccc)[2:]) + ":" + str(freq_str))

        line = k + ";" + ";".join(segments)
        lines.append(line)
    lines = "\n".join(lines)
    out.write(lines)

    # cleanup
    doc_mem = 0
    chunk_no += 1
    indexed_dict = {}


START_LINK = "startoflink"

# title: 0, info: 1, body: 2, cat: 3, refs: 4, links: 5


class WikiParser(xml.sax.ContentHandler):
    def __init__(self):
        super().__init__()
        self.CurrentData = ""
        self.currentPage: Page = Page(-1)

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        global doc_id, doc_mem
        if tag == TAG_PAGE:
            self.currentPage = Page(doc_id)
            doc_id += 1
            doc_mem += 1
            if doc_mem >= DOC_IN_MEM:
                dump_index()

    def endElement(self, tag):
        if tag != TAG_PAGE:
            return
        # global id_to_title, totalToken

        # id_to_title[self.currentPage.doc_no] = self.currentPage.title
        # print(self.currentPage)
        if self.currentPage and self.currentPage.doc_no % OUTPUT_DELTA == 0:
            print(self.currentPage.doc_no, file=sys.stderr)
        body = " ".join(self.currentPage.body)

        categories_str = re.findall("(?<=\[\[Category:)(.*?)(?=\]\])", body)
        ref_type_1 = []
        # print("ref type 1 ", ref_type_1)
        ref_type_3 = re.findall(r"<ref(.+?)>", body)
        lis = re.split(
            r"==References==|== References ==|== references ==|==references==",
            body,
            1,
        )
        if len(lis) > 1:
            ref_type_1 = [re.split(r"==|<|\[\[", lis[1])[0]]
        # ref_type_3 = re.findall(r'&lt;ref name=(.+?)&gt;', body)
        # ref_type_3 = re.findall(r'&lt;ref name=&quot;(.+?)&quot;', body)
        # print(self.currentPage)
        # print(ref_type_1)
        infobox = get_infobox(body)
        # get links
        lis = re.split(r"==External links==|== External links ==", body, 1)
        link_tokens = []
        if len(lis) > 1:
            lis = re.split(r"==|\[\[", lis[1], 1)[0]
            link_tokens = tokenizer(lis)
        # print(infobox)
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

        body = body.replace("==External links==", START_LINK)
        tokens = tokenizer(body)
        # print("Tokens", tokens)

        # print(tokens)
        # link_tokens = []
        body_tokens = []
        for token in tokens:
            if token == START_LINK:
                break
            body_tokens.append(token)

        # print(link_tokens)
        idx = self.currentPage.doc_no
        title = " ".join(self.currentPage.title)
        title_tokens = tokenizer(title)
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


field_map = {0: "z", 1: "y", 2: "x", 3: "v", 4: "u", 5: "t"}


def main():
    global output_folder
    dump_location, output_folder, stats_file = (
        sys.argv[1],
        sys.argv[2],
        sys.argv[3],
    )
    if output_folder[-1] == "/":
        output_folder = output_folder[:-1]
    print(dump_location, output_folder, stats_file)
    for word in stopword + mystopwords:
        word_set[word] = None
    handler = WikiParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(dump_location)
    dump_index()
    # pickle.dump(indexed_dict, pickle_out)
    # pickle_out = open(f"{output_folder}/id_to_title.pickle", "wb+")
    # pickle.dump(id_to_title, pickle_out)
    with open(stats_file, "w+") as text_file:
        # text_file.write(f"{len(all_tokens)}\n{len(indexed_dict)}")
        text_file.write(f"{chunk_no}\n{len(indexed_dict)}")
    # with open("keys.txt", "w+") as text_file:
    #     json.dump(list(sorted(indexed_dict.keys())), text_file)


if __name__ == "__main__":
    main()
