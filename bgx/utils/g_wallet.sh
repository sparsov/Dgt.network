addr=$1
addr=${addr:="4aa37a37b9793a7f3696129d9a367b26fd0b2b1c"}
echo addr ${addr}
curl http://18.222.233.160:8008/wallets/${addr}
