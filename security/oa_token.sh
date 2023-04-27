client_id=test
client_secret=testsecret
username=test
code=json
#curl -u ${client_id}:${client_secret} -XPOST http://127.0.0.1:8003/token -F grant_type=password -F username=${username} -F password=valid -F scope=profile
client_id=sparsov
client_secret=Ghbdtnueuk.1964
# https://github.com/login/oauth/authorize https://github.com/login/oauth/access_token
curl -u ${client_id}:${client_secret} -XPOST https://github.com/login/oauth/authorize -F grant_type=authorization_code -F scope=profile -F code=${code}
