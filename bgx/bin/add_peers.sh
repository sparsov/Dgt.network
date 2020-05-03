#!/bin/bash
IFS=";"; declare -a Array=($1)
for x in "${Array[@]}"
 do
    echo  "$x" >> /etc/hosts
 done
