#!/bin/bash
#for clust in 1 #2 3 4 5 6
#do
#  for peer in 1 #2 3  
#  do
#    echo The  clusters/$clust/$peer item
#    #ls clusters/$clust/$peer
#    #bgx dag show nest --url http://bgx-api-c$clust-$peer:8609
#  done
#done
#
#
bgx dag show nest --url http://bgx-api-c1-2:8009;echo =====
bgx dag show nest --url http://bgx-api-c2-2:8209;echo =====
bgx dag show nest --url http://bgx-api-c3-2:8309;echo =====
bgx dag show nest --url http://bgx-api-c4-2:8409;echo =====
bgx dag show nest --url http://bgx-api-c5-2:8509;echo =====
bgx dag show nest --url http://bgx-api-c6-2:8609




