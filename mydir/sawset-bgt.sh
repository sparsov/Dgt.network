sawset proposal create \
  --url http://rest-api:8008 \
  --key /root/.sawtooth/keys/my_key.priv \
  sawtooth.validator.transaction_families='[{"family": "intkey", "version": "1.0"}, {"family":"sawtooth_settings", "version":"1.0"}]'
