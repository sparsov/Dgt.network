key=$1
key=${key:="0281e398fc978e8d36d6b2244c71e140f3ee464cb4c0371a193bb0a5c6574810ba"}
curl -X POST -H "public_key:${key}" http://18.222.233.160:8008/wallets
