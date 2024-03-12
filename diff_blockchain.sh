#!/usr/bin/env bash

if [[ $1 == "" ]]; then
    echo "ERROR: You need to pass the number of nodes as a command line argument."
    exit
fi

fpath="./"
fname="blockchain"
fextension=".txt"

i=1
f1=$fpath$fname"0"$fextension

while [[ $i != $1 ]]; do
    f2=$fpath$fname$i$fextension
    s=$(diff $f1 $f2)

    if [[ $s != "" ]]; then
        echo "blockchain differs for nodes 0 and "$i
    fi
    i=$(( i + 1 ))
done