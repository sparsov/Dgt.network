#!/bin/bash
for clust in c1 c2 c3 c4 c5 c6
do
  for peer in dgt1 dgt2 dgt3 dgt4 dgt5 dgt6  
  do
    echo The  clusters/$clust/$peer item
    #ls clusters/$clust/$peer
    rm -f clusters/$clust/$peer/data/* clusters/$clust/$peer/logs/*.log*;
  done
done





