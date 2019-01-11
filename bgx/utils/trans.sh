from=$1
from=${from:="MDI4MWUzOThmYzk3OGU4ZDM2ZDZiMjI0NGM3MWUxNDBmM2VlNDY0Y2I0YzAzNzFhMTkzYmIwYTVjNjU3NDgxMGJh"}
to=$2
to=${to:="MDI4YzdlMDZkYjNhZjUwYTk5NTgzOTBlM2UyOWYxNjZiMWNmNjE5ODU4NmFjZjM3Y2RlNDZjOGVhNTRlNGE3OWVm"}
num=$3
num=${num:=1}
post="{\"data\": {\"payload\" : {\"address_from\": \"${from}\",\"address_to\":\"${to}\",\"tx_payload\" : ${num}},\"signed_payload\": \"\"}}"
echo POST  $post
curl -X POST -d "$post" http://18.222.233.160:8008/transactions
