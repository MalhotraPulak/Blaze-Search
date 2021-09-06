rm -rf $2
mkdir -p $2
time python3 parser.py $1 $2 $3
