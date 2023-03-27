openssl req -newkey rsa:4096 -x509 -sha256 -days 365 -nodes -out example.crt -keyout example.key -subj "/C=US/ST=New York/L=Brooklyn/O=Example, Inc./OU=IT/CN=example.com"
