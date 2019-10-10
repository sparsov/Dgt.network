#!/bin/bash
for clust in c1 c2 c3 c4 c5 c6
do
  for peer in bgx1 bgx2 bgx3 bgx4 bgx5 bgx6  
  do
    echo The  clusters/$clust/$peer item
    #ls clusters/$clust/$peer
    rm -f clusters/$clust/$peer/data/* clusters/$clust/$peer/logs/*.log*;
  done
done





