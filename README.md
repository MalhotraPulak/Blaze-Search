## BLAZE SEARCH ENGINE
A fast wikipedia search engine with support for field queries and returns the top 10 relevant document titles using tf-idf score. 

The search time depends upon query length. For queries of length less than 5, the search time is less than 6 seconds in most cases for the wikipedia dump at the moment. (79 gb in size)

Fields supported:
- Title (t)
- Infobox (i)
- Body (b)
- Links (l)
- References (r)
- Categories (c)

### Setup and use
Clone the repository
```bash
git clone https://github.com/PulakIIIT/Blaze-Search Blaze-Search
cd Blaze-Search
```
Create a python virtual environment
```bash
python3 -m venv venv
pip3 install -r requirements.txt
cd src 
```

#### Create an index
```bash
python3 index.py <location of wiki dump> <location of output folder> <location of stats file>
```
The intermediate mini indices are created in the output folder
To merge the mini indices to form the final indices:
```bash
python3 merger.py <location of mini indices> <final output folder>
```
Store the title mapping separately 
```bash
python3 title_parser.py <location of wiki dump> <title output folder>
```

#### Run search on a set of queries
Create a file with one query per line
``` bash
cat > queries.txt
```
Run the search with this `queries.txt` file 

```bash
python3 search.py queries.txt <location of index> <location of title mappings>
```

The results are stored in an output file `queries_op.txt`.

Example  
Sample input (`queries.txt`): 
```
t:Silicon Valley l:imdb
Hunger Games
b:Barack Obama t:President
Speed of Light
Alan Turing
```

Sample output (`queries_op.txt`):
```

t:Silicon Valley l:imdb

13211768, Silicon Valley (TV series) 
18883293, Silicon Valley (season 2) 
15073764, Silicon Valley (season 1) 
18883315, Silicon Valley (season 4) 
18883321, Silicon Valley (season 5) 
18883307, Silicon Valley (season 3) 
253494, Pirates of Silicon Valley 
19399298, Silicon Valley (season 6) 
17623, Silicon Valley 
11806935, Start-Ups: Silicon Valley 
Time taken 3.4127981662750244

Hunger Games 

9976420, The Hunger Games (film) 
12587727, The Hunger Games: Mockingjay – Part 2 
12587724, The Hunger Games: Mockingjay – Part 1 
11435615, The Hunger Games: Catching Fire 
14042352, The Hunger Games: Mockingjay, Part 1 (soundtrack) 
6639548, The Hunger Games (novel) 
9976489, The Hunger Games 
12936509, The Hunger Games (film series) 
12928086, The Hunger Games: Catching Fire – Original Motion Picture Soundtrack 
11081795, The Hunger Games: Songs from District 12 and Beyond 
Time taken 4.047765016555786

b:Barack Obama t:President

6627805, Presidency of Barack Obama 
328672, Barack Obama 
6933136, Timeline of the Barack Obama presidency (2009) 
6794261, First inauguration of Barack Obama 
5946579, Family of Barack Obama 
15310131, Timeline of the Barack Obama presidency (2016–January 2017) 
6686624, Nationwide opinion polling for the 2012 United States presidential election 
3508836, Barack Obama 2008 presidential primary campaign 
5277310, List of Barack Obama 2008 presidential campaign endorsements 
12107566, Timeline of the Barack Obama presidency (2013) 
Time taken 3.3808069229125977

Speed of Light 

18774, Speed of light 
7998952, The Sound the Speed the Light 
319214, Need for Speed 
13173208, A Slower Speed of Light 
12680499, CBD and South East Light Rail 
5446, Docklands Light Railway 
11927612, Need for Speed (film) 
4648487, Speed of gravity 
108924, MAX Light Rail 
12301530, Speed of Light (Speed song) 
Time taken 2.8875961303710938

Alan Turing

473, Alan Turing 
19847992, Prof: Alan Turing Decoded 
18232863, Statue of Alan Turing 
17127170, Alan Turing: The Enigma 
4269288, Alan Turing Building 
13421176, Alan Turing Institute 
17648093, Dermot Turing 
20265, Turing Award 
7317585, Alan Turing Year 
11458043, Alan Turing Centenary Conference 
Time taken 2.3075718879699707

```

### Indexing
To index the 79 gb wiki dump we follow the steps: 

*  **Parsing and Chunkwise blocking:**<br/>
The XML SAX parser has been used to parse the XML files containing the wiki dump. For every 100000 pages are read by the parser, the text of the article, the title and the IDs of these 100000 pages are stored in memory. After 100000 pages are read, the data in memory is then processed and written to a mini index file. 
To support field queries, the different components of a document are split using *regex* and text matching techniques. All the text is processed by case folding (lowercase), tokenization, stop words removal and stemming. 
There were a total of 214 such mini index files created. This is the most time consuming step and took approximately 14 hours.

*  **Merging mini index files and splitting alphabetically** <br/>
These mini indices are merged by using a merged sort like technique and split into around 19000 files. Each of these file has a 3 letter filename `f` then it contains all the indexed tokens that start with `f`.

*  **Convention followed in the index** <br/>
Each posting list has a list of documents and the associated frequencies for the different fields in the wiki article. Since the data is stored in ASCII, to make slightly more efficient the document ids are stored in hexadecimal. Example: `catabus;28b0cf:x5;29762c:y4x19u2t1;671b60:x3;7c3f08:p;84bf48:x3;9e7` 
``

### Searching Mechanism

The search script produces results for top 10 documents. 
The query text is first processed via the same text processing as in the index creation. The tokens are then segregated to split the field queries (if any). The posting lists of the words in the query are then retrieved from the corresponding letters' index files. The posting list retrieval is done in parallel for each word to make the search fast.

Once the posting lists have been retrieved, each document in the posting list is assigned a score. This socre is computed via the ***Tf-IDf principle***. The formula for the weight of a word ***i*** in a document ***j*** ie: ***w<sub>i,j</sub>*** is : 

***w<sub>i,j</sub> = (1+ log<sub>10</sub>(tf<sub>i,j</sub>)) log<sub>10</sub>(N/di)***

This is to prevent accounting for any kind of term spamming.





