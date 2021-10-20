import xml.sax
from typing import List

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
        print("Titl", ' '.join(self.title))
        # print("Info", self.infobox)
        # print("Cat", self.category)
        # print("Links", self.links)
        # print("Refs", self.references)
        print("----End Doc---")
        return ""


TAG_PAGE = "page"
TAG_TITLE = "title"

doc_id = 0

DOC_IN_MEM = 50000
OUTPUT_DELTA = 5000

indexed_dict = {}
# id_to_title = {}

def dump_title():
    global chunk_no, indexed_dict, doc_mem
    print("writing title file", doc_id)
    # write the current index to memory
    out = open(f"/scratch/pulak/titles/title{chunk_no}.txt", "w+")
    # out = open(f"./titles/title{chunk_no}.txt", "w+")
    lines = []
    for k, v in sorted(indexed_dict.items()):
        lines.append(f"{k}!!{v}")
    data = "\n".join(lines)
    out.write(data)
    out.close()
    # cleanup 
    doc_mem = 0
    chunk_no += 1
    indexed_dict = {}


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
            if doc_mem >= DOC_IN_MEM:
                dump_title()            
            doc_mem += 1
            doc_id += 1

    def endElement(self, tag):
        if tag != TAG_PAGE:
            return
        title = ' '.join(self.currentPage.title)
        indexed_dict[self.currentPage.doc_no] = title
        
    def characters(self, content):
        if self.CurrentData == TAG_TITLE:
            self.currentPage.title.append(content)


import sys

def main():
    dump_location = sys.argv[1]
    handler = WikiParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.parse(dump_location)
    dump_title()

if __name__ == "__main__":
    main()
