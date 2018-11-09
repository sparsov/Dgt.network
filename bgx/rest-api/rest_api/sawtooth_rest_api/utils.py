import ecdsa
import base64
from Crypto.Hash import keccak
import chilkat
import json
# import sawtooth_rest_api.exceptions as errors

# Unlock chilkat library
chilkat.CkGlobal().UnlockBundle("Anything for 30-day trial")


def generate_keys_pair():
    """
    :return: tuple of serialized secp256k1 elliptic curve private and public keys in Pkcs1 DER format in base64 encode
    """
    fortuna = chilkat.CkPrng()
    entropy = fortuna.getEntropy(32,"base64")
    fortuna.AddEntropy(entropy,"base64")
    ecc = chilkat.CkEcc()
    priv_key = ecc.GenEccKey("secp256k1", fortuna)
    pub_key = priv_key.GetPublicKey()
    return priv_key.getPkcs1ENC('base64'), pub_key.getEncoded(True, 'base64')


def eth_address_from_pub_key(pkcs1_DER_base64_pub_key):
    """
    :param pkcs1_DER_base64_pub_key: secp256k1 elliptic curve public key in Pkcs1 DER format in base64 encode
    :return: ethereum standart address - hex encoded the last 20 bytes of keccak 256 hash of public key
    """
    try:
        ecdsa_pub_key = ecdsa.VerifyingKey.from_der(base64.b64decode(pkcs1_DER_base64_pub_key))
    except TypeError:
        raise errors.InvalidPublicKey()
    public_key_bytes = ecdsa_pub_key.to_string()
    keccak_hash = keccak.new(digest_bits=256)
    keccak_hash.update(public_key_bytes)
    keccak_digest = keccak_hash.hexdigest()
    # Take the last 20 bytes
    address_len = 40
    address = keccak_digest[-address_len:]
    return address


def hash_dict(dict):
    """
    :param dict: utf-8 charset dictionary to hash
    :return: sha256 hashed and base64 encoded json serialization of dict
    """
    crypt = chilkat.CkCrypt2()
    crypt.put_HashAlgorithm("SHA256")
    crypt.put_Charset("utf-8")
    crypt.put_EncodingMode("base64")

    json_serialized_dict = json.dumps(dict, sort_keys=True)

    return crypt.hashStringENC(json_serialized_dict)


# dict = {
#         "public_key_hashed": "HKJEk_ov0wgRsmi6_o8pL9pSEBbIHvgmLGto7LaT3fM",
#         "tx_payload": 10,
#         "coin_code": "dec"
#     }
def sign_dict(priv_key, dict):
    """
    :param priv_key: secp256k1 elliptic curve private key in Pkcs1 DER format in base64 encode
    :param dict: utf-8 charset dictionary to sign
    :return: secp256k1 signed sha256 hashed and base64 encoded json serialization of dict
    """
    sha256_hash = hash_dict(dict)

    chilkat_ecdsa = chilkat.CkEcc()
    prng = chilkat.CkPrng()

    chilkat_byte_data = chilkat.CkByteData()
    chilkat_byte_data.appendEncoded(priv_key, 'base64')
    chilkat_private_key = chilkat.CkPrivateKey()
    chilkat_private_key.LoadPkcs1(chilkat_byte_data)

    ecdsa_sig_base64 = chilkat_ecdsa.signHashENC(sha256_hash,"base64",chilkat_private_key,prng)
    return ecdsa_sig_base64


def verify_signature(pub_key, signature, dict):
    """
    :param pub_key: secp256k1 elliptic curve public key in Pkcs1 DER format in base64 encode
    :param signature: secp256k1 signed sha256 hashed and base64 encoded json serialization of dict
    :return: result of verification, bool
    """
    chilkat_ecdsa = chilkat.CkEcc()
    sha256_hash = hash_dict(dict)

    chilkat_pub_key = chilkat.CkPublicKey()
    success = chilkat_pub_key.LoadBase64(pub_key)
    if not success:
        print(chilkat_pub_key.lastErrorText())
        raise errors.InvalidPublicKey()

    return chilkat_ecdsa.VerifyHashENC(sha256_hash, signature, "base64", chilkat_pub_key)


def generate_startup_global_state():
    generated_keys = generate_keys_pair()
    node_state = {
        'private_key': generated_keys[0],
        'public_key': generated_keys[1],
        'address': eth_address_from_pub_key(generated_keys[1]),
        'wallet': {
            'dec': 100,
            'bgt': 100000
        }
    }
    user_keys = []
    users_wallets = [
        {'dec': 20}, {'dec': 50}, {'dec': 80}, {'bgt': 100}, {'bgt': 200},
        {'bgt': 300}, {'bgt': 400}, {'bgt': 500}, {'bgt': 600}, {'bgt': 700},
    ]
    for i in range(10):
        generated_keys = generate_keys_pair()
        user_keys.append({
            'private_key': generated_keys[0],
            'public_key': generated_keys[1],
            'address': eth_address_from_pub_key(generated_keys[1]),
            'wallet': users_wallets[i]
        })
    print({'node': node_state, 'users': user_keys})

print(sign_dict('MC4CAQEEILNcUpk4Ez03Q5tTstifDv4Edc3A+UFOq9swX31metuzoAcGBSuBBAAK', {
                        "address_to": "eb442acf33c0294d2541ac145a929e4ea98679f5",
                        "tx_payload": 100,
                        "coin_code": "bgt",
                        "reason": "any reason to add funds"
                }))
print(verify_signature('MFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAEmJmaAf5EqvbfEWtJJRR8pOmlBrNETY0dyg+ArMzEBxF2HmgpSw2t8/2+PgveIROgVhJwxfIVDI7DiJjDjc0JRw==',
                       'MEQCIAL8AS+SpsGQ95BS//oCaXVvlpioRmn5Zg0EQUoZxWZ/AiAJmdly8GuHEL0vsSEIM7h+pH8AM8PZ+zMe5Usftt/JYw==',
                       {
                           "address_to": "eb442acf33c0294d2541ac145a929e4ea98679f5",
                           "tx_payload": 100,
                           "coin_code": "bgt",
                           "reason": "any reason to add funds"
                       }
                       ))