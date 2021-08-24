dpkg -l |tail -n+6 |awk '{print($2)}'| tr '\n' ' '
