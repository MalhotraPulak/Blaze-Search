#time python3 2019101050/parser.py wiki.xml output/ stats.txt > dump.txt
python3 2019101050/search.py queries.txt
echo "----------------- QUERIES_OP START -------------------"
cat queries_op.txt
echo "----------------- QUERIES_OP END -------------------"
# time python3 search.py output "c:Zambian"
# time python3 search.py output/ "l:veikkausliiga"
# time python3 search.py output  "stephen kunda"
# time python3 search.py output "r:Imdb"
# time python3 search.py output "Pop"
