import sawtooth_sdk
import cbor
import urllib.request
import hashlib

from urllib.error import HTTPError

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from hashlib import sha512
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchList

# state 1cf126112e7d59dd491d07f7a6e6ba7cae6030136a4c4f1a061c676fdad4a3642d4040 (70 chars)
#Creating a Private Key and Signer
#In order to confirm your identity and sign the information you send to the validator, you will need a 256-bit key.
# Sawtooth uses the secp256k1 ECDSA standard for signing, which means that almost any set of 32 bytes is a valid key.
#  It is fairly simple to generate a valid key using the SDK’s signing module.
context = create_context('secp256k1')
private_key = context.new_random_private_key()
signer = CryptoFactory(context).new_signer(private_key)

#Encoding Your Payload
# Transaction payloads are composed of binary-encoded data that is opaque to the validator. 
# The logic for encoding and decoding them rests entirely within the particular Transaction Processor itself.
# As a result, there are many possible formats, and you will have to look to the definition of the Transaction Processor itself for that information.
# As an example, the IntegerKey Transaction Processor uses a payload of three key/value pairs encoded as CBOR. Creating one might look like this:
payload = {
    'Verb': 'set',
    'Name': 'openThedoor2',
    'Value': 21}

payload_bytes = cbor.dumps(payload)

# Building the Transaction

# Transactions are the basis for individual changes of state to the Sawtooth blockchain.
#  They are composed of a binary payload, a binary-encoded TransactionHeader with some cryptographic safeguards and metadata about how it should be handled,
#  and a signature of that header. It would be worthwhile to familiarize yourself with the information in Transactions and Batches, 
#  particularly the definition of TransactionHeaders.
# 1. Create the Transaction Header
# A TransactionHeader contains information for routing a transaction to the correct transaction processor, what input and output state addresses are involved,
# references to prior transactions it depends on, and the public keys associated with the its signature.
# The header references the payload through a SHA-512 hash of the payload bytes.
addr = hashlib.sha512('bgt'.encode('utf-8')).hexdigest()[0:6] + hashlib.sha512(payload['Name'].encode('utf-8')).hexdigest()[-64:]

txn_header_bytes = TransactionHeader(
    family_name='bgt', #'intkey',
    family_version='1.0',
    inputs = [addr], 
    outputs= [addr],
    signer_public_key=signer.get_public_key().as_hex(),
    # In this example, we're signing the batch with the same private key,
    # but the batch can be signed by another party, in which case, the
    # public key will need to be associated with that key.
    batcher_public_key=signer.get_public_key().as_hex(),
    # In this example, there are no dependencies.  This list should include
    # an previous transaction header signatures that must be applied for
    # this transaction to successfully commit.
    # For example,
    # dependencies=['540a6803971d1880ec73a96cb97815a95d374cbad5d865925e5aa0432fcf1931539afe10310c122c5eaae15df61236079abbf4f258889359c4d175516934484a'],
    dependencies = [],#['98e73b821521542a6ee8b1b4ad301b063676690670b55cf6e5af3b398e6e5a5511f6ec14eedd3af470d38f3cccf91f686b2b00357b3e3072bd4102dc22924796'],
    payload_sha512=sha512(payload_bytes).hexdigest()
).SerializeToString()

# 2. Create the Transaction
#Once the TransactionHeader is constructed, its bytes are then used to create a signature. This header signature also acts as the ID of the transaction.
#The header bytes, the header signature, and the payload bytes are all used to construct the complete Transaction.

signature = signer.sign(txn_header_bytes)
print('signature',signature)
txn = Transaction(
    header=txn_header_bytes,
    header_signature=signature,
    payload= payload_bytes
)

#3. (optional) Encode the Transaction(s)
#If the same machine is creating Transactions and Batches there is no need to encode the Transaction instances.
# However, in the use case where Transactions are being batched externally, they must be serialized before being transmitted to the batcher.
# The Python 3 SDK offers two options for this. One or more Transactions can be combined into a serialized TransactionList method,
# or can be serialized as a single Transaction.

txn_list_bytes = TransactionList(
    transactions=[txn] # [txn1, txn2]
).SerializeToString()

txn_bytes = txn.SerializeToString()

# Building the Batch
# Once you have one or more Transaction instances ready, they must be wrapped in a Batch. Batches are the atomic unit of change in Sawtooth’s state.
# When a Batch is submitted to a validator each Transaction in it will be applied (in order), or no Transactions will be applied.
# Even if your Transactions are not dependent on any others, they cannot be submitted directly to the validator. They must all be wrapped in a Batch.
# 1. Create the BatchHeader
# Similar to the TransactionHeader, there is a BatchHeader for each Batch. As Batches are much simpler than Transactions,
# a BatchHeader needs only the public key of the signer and the list of Transaction IDs, in the same order they are listed in the Batch.
txns = [txn]

batch_header_bytes = BatchHeader(
    signer_public_key=signer.get_public_key().as_hex(),
    transaction_ids=[txn.header_signature for txn in txns],
).SerializeToString()

# 2. Create the Batch
#  Using the SDK, creating a Batch is similar to creating a transaction. The header is signed, and the resulting signature acts as the Batch’s ID.
#  The Batch is then constructed out of the header bytes, the header signature, and the transactions that make up the batch.
signature = signer.sign(batch_header_bytes)

batch = Batch(
    header=batch_header_bytes,
    header_signature=signature,
    transactions=txns
)
# 3. Encode the Batch(es) in a BatchList
# In order to submit Batches to the validator, they must be collected into a BatchList. Multiple batches can be submitted in one BatchList,
# though the Batches themselves don’t necessarily need to depend on each other. Unlike Batches, a BatchList is not atomic.
# Batches from other clients may be interleaved with yours.

batch_list_bytes = BatchList(batches=[batch]).SerializeToString()
# save for curl
output = open('bgt.batches', 'wb')
output.write(batch_list_bytes)

# Submitting Batches to the Validator
# The prescribed way to submit Batches to the validator is via the REST API. This is an independent process that runs alongside a validator,
# allowing clients to communicate using HTTP/JSON standards. Simply send a POST request to the /batches endpoint, 
# with a “Content-Type” header of “application/octet-stream”, and the body as a serialized BatchList.
try:
    request = urllib.request.Request(
        'http://rest-api:8008/batches',
        batch_list_bytes,
        method='POST',
        headers={'Content-Type': 'application/octet-stream'})
    response = urllib.request.urlopen(request)
    print('resp',response)

except HTTPError as e:
    response = e.file
