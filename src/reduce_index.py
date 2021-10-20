import os
import math

field_map = {
    "z": 0,
    "y": 1,
    "x": 2,
    "v": 3,
    "u": 4,
    "t": 5,
    "p": 2,
    "q": 1,
}

TOTAL_DOCS = 22000000
WEIGHTS = [2, 2, 1, 3, 2, 2]


def reduce_file(file):
    print(file)
    dir_name = "./scratch/pulak/reducedIndex3/"
    f = open("./scratch/pulak/mergedIndex3/" + file, "r")
    lines = f.readlines()
    f.close()
    out_lines = []
    for line in lines:
        tokens = line.strip().split(";")
        word = tokens[0]
        tokens = tokens[1:]
        # print("Found", word, file=sys.stderr)
        new_docs = []
        doc_list = tokens
        idf = math.log10(TOTAL_DOCS / len(doc_list))
        field_names = list(field_map.keys())
        # print(len(tokens))
        for segment in doc_list:
            doc_id_freq = segment.split(":")
            # doc_id = int(doc_id_freq[0], base=16)
            freq_str = str(doc_id_freq[1]) + "z"
            last = ""
            freq = 0
            score = 0
            # sol = False
            # if doc_id == 4845579:
            #     sol = True
            #     print(freq_str)

            for c in freq_str:
                if c in field_names:
                    bonus = 1
                    if c == "p":
                        score += WEIGHTS[2] * idf * bonus
                    elif c == "q":
                        score += WEIGHTS[1] * idf * bonus
                    if freq != 0 and last:
                        # if sol:
                        #     print("before", score, freq, bonus)
                        score += (
                            WEIGHTS[field_map[last]]
                            * (1 + math.log10(freq))
                            * idf
                            * bonus
                        )
                        # if sol:
                        #     print("after", score)
                        freq = 0
                    last = c
                else:
                    freq = freq * 10 + int(c)
            if score < 1:
                continue
            new_docs.append(segment)
        data = word + ";" + ";".join(new_docs)
        out_lines.append(data)
    out_file = open(dir_name + file, "w")
    out_file.write("\n".join(out_lines))
    out_file.close()


def main():
    files = sorted(list(os.listdir("./scratch/pulak/mergedIndex3")))
    for file in files:
        reduce_file(file)
    pass


if __name__ == "__main__":
    main()
