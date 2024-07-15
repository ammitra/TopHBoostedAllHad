#!/bin/bash
for s in TprimeB-1800-125; do
    for y in 16 16APV 17 18; do
        for v in None PNetTop_up PNetTop_down PNetXbb_up PNetXbb_down JES_up JES_down JER_up JER_down JMS_up JMS_down JMR_up JMR_down; do
            echo 'python THselection.py -s '"$s"' -y '"$y"' --HT 750 -v '"$v"
            python THselection.py -s $s -y $y --HT 750 -v $v
        done;
    done;
done;
