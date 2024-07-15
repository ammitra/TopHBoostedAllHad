#!/bin/bash
for s in ttbar-allhad; do
    for y in 18; do
        for v in None PNetTop_up PNetTop_down PNetXbb_up PNetXbb_down DAK8Top_up DAK8Top_down; do
            echo 'python THselection.py -s '"$s"' -y '"$y"' --HT 750 -v '"$v"' -n 10 -j 1'
            python THselection.py -s $s -y $y --HT 750 -v $v -n 10 -j 1
        done;
    done;
done;
