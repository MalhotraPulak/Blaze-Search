from heapq import heapify, heappush, heappop

FILES = 214

class FileIter:
    def __init__(self, iterat, tokens, file_no):
        self.iterat = iterat
        self.tokens = tokens 
        self.file_no = file_no
        self.token = tokens[0]


    def __lt__(self, other):
        if self.token == other.token:
            return self.file_no < other.file_no
        return self.token < other.token

    def get_next(self):
        text = self.iterat.readline().strip()
        if not text:
            return -1
        self.tokens = text.split(";")
        self.token = self.tokens[0]
        return 0


    def get_docs(self):
        return self.tokens[1:]



def main():
    file_iters = []
    last_open = None
    out_file = None
    for i in range(FILES):
        f = open(f"/scratch/pulak/output/index{i}.txt", "r")
        # f = open(f"./mini_indices/index{i + 97}.txt", "r")
        tokens = f.readline().strip().split(";")
        file_iters.append(FileIter(f, tokens, i))

    heapify(file_iters)

    while file_iters:
        smallestIter = heappop(file_iters)
        token = smallestIter.token
        if token[0] != last_open:
            if out_file:
                out_file.close()
            last_open = token[0]
            out_file = open(f"/scratch/pulak/mergedIndex/{last_open}.txt", "w+")
            print("Writing to", last_open)
        docs_list = []
        docs_list.extend(smallestIter.get_docs())
        if smallestIter.get_next() != -1:
            heappush(file_iters, smallestIter)


        while file_iters and file_iters[0].token == token:
            old_file = heappop(file_iters)
            docs_list.extend(old_file.get_docs()) 
            if old_file.get_next() != -1:
                heappush(file_iters, old_file)
            
        line = token + ";" + ';'.join(docs_list) + "\n"
        if out_file:
            out_file.write(line) 




if __name__ == "__main__":
    main()
