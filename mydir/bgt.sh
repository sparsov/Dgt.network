sawset -v proposal create \
  --url http://rest-api:8008 \
  --key /root/.sawtooth/keys/my_key.priv  \
  sawtooth.validator.transaction_families='[{"family": "bgt", "version": "1.0"}, {"family":"sawtooth_settings", "version":"1.0"}]'
