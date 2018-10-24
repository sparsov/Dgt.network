sawset -v proposal create \
  --url http://rest-api:8008 \
  sawtooth.validator.transaction_families='[{"family": "bgt", "version": "1.0"}, {"family":"sawtooth_settings", "version":"1.0"}]'
