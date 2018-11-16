# Copyright 2018 NTRLab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import logging
import hashlib

import cbor
#from  web3  import Web3, HTTPProvider

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
#from sawtooth_signing.secp256k1 import Secp256k1PrivateKey
from smart_bgt.processor.utils  import FAMILY_NAME,FAMILY_VER,make_smart_bgt_address,SMART_BGT_ADDRESS_PREFIX #
from sawtooth_signing.secp256k1 import Secp256k1Context, Secp256k1PrivateKey, Secp256k1PublicKey
#from ecdsa import SigningKey, SECP256k1

#import smart_bgt.processor.emission as emission
#from smart_bgt.processor.services import DigitalSignature
from smart_bgt.processor.services import BGXCrypto,BGXlistener
from smart_bgt.processor.token import Token
from smart_bgt.processor.emission import EmissionMechanism
#from smart_bgt.processor.emission import Token
#from sawtooth_signing.secp256k1 import Secp256k1Context 


LOGGER = logging.getLogger(__name__)

VALID_VERBS = 'set', 'inc', 'dec' , 'init', 'generate_key'

MIN_VALUE = 0
MAX_VALUE = 4294967295
MAX_NAME_LENGTH = 20

#FAMILY_NAME = 'smart-bgt'
#FAMILY_VER  = '1.0'

#SMART_BGT_ADDRESS_PREFIX = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]


#def make_smart_bgt_address(name):
#    return SMART_BGT_ADDRESS_PREFIX + hashlib.sha512(name.encode('utf-8')).hexdigest()[-64:]


class SmartBgtTransactionHandler(TransactionHandler):
    @property
    def family_name(self):
        return FAMILY_NAME

    @property
    def family_versions(self):
        return [FAMILY_VER]

    @property
    def namespaces(self):
        return [SMART_BGT_ADDRESS_PREFIX]

    def apply(self, transaction, context):
        LOGGER.info('SmartBgtTransactionHandler apply')
        verb, name, value, value_2 = _unpack_transaction(transaction)
        LOGGER.info('SmartBgtTransactionHandler verb=%s name %s',verb,name)
        state = _get_state_data(name, context)
        LOGGER.info('SmartBgtTransactionHaEmissionMechanismndler _do_smart_bgt')
        updated_state = _do_smart_bgt(verb, name, value, value_2, state)

        _set_state_data(name, updated_state, context)
    

def _unpack_transaction(transaction):
    verb, name, value, value_2 = _decode_transaction(transaction)

    #_validate_verb(verb)
    #_validate_name(name)
    #_validate_value(value)

    return verb, name, value, value_2


def _decode_transaction(transaction):
    try:
        content = cbor.loads(transaction.payload)
    except:
        raise InvalidTransaction('Invalid payload serialization')

    try:
        verb = content['Verb']
    except AttributeError:
        raise InvalidTransaction('Verb is required')

    try:
        name = content['Name']
    except AttributeError:
        raise InvalidTransaction('Name is required')

    try:
        value = content['Value']
    except AttributeError:
        raise InvalidTransaction('Value is required')

    try:
        value_2 = content['Value_2']
    except AttributeError:
        raise InvalidTransaction('Value is required')

    return verb, name, value, value_2


def _validate_verb(verb):
    if verb not in VALID_VERBS:
        raise InvalidTransaction('Verb must be "set", "inc", "init" or "dec"')


def _validate_name(name):
    if not isinstance(name, str) or len(name) > MAX_NAME_LENGTH:
        raise InvalidTransaction(
            'Name must be a string of no more than {} characters'.format(
                MAX_NAME_LENGTH))


def _validate_value(value):
    if not isinstance(value, int) or value < 0 or value > MAX_VALUE:
        raise InvalidTransaction(
            'Value must be an integer '
            'no less than {i} and no greater than {a}'.format(
                i=MIN_VALUE,
                a=MAX_VALUE))


def _get_state_data(name, context):
    address = make_smart_bgt_address(name)

    state_entries = context.get_state([address])

    try:
        return cbor.loads(state_entries[0].data)
    except IndexError:
        return {}
    except:
        raise InternalError('Failed to load state data')


def _set_state_data(name, state, context):
    address = make_smart_bgt_address(name)

    encoded = cbor.dumps(state)

    addresses = context.set_state({address: encoded})

    if not addresses:
        LOGGER.debug('_set_state_data  State error')
        raise InternalError('State error')
    LOGGER.debug('_set_state_data  DONE encoded=%s address=%s',encoded,address)

def _do_smart_bgt(verb, name, value, value_2, state):
    verbs = {
        'set': _do_set,
        'inc': _do_inc,
        'dec': _do_dec,
        'init': _do_init
    }
    LOGGER.debug('_do_smart_bgt request name=%s, value=%s',name, value)

    if name == 'None':
        return _do_generate_key(state)

    if value_2:
        return _do_init(name, value, value_2, state)

    try:
        return verbs[verb](name, value, state)
    except KeyError:
        # This would be a programming error.
        raise InternalError('Unhandled verb: {}'.format(verb))


def _do_set(name, value, state):
    msg = 'Setting "{n}" to {v}'.format(n=name, v=value)
    LOGGER.debug(msg)
    

    if name in state:
        raise InvalidTransaction(
            'Verb is "set", but already exists: Name: {n}, Value {v}'.format(
                n=name,
                v=state[name]))

    updated = {k: v for k, v in state.items()}
    updated[name] = value
    LOGGER.debug("_do_set  updated=%s ",updated)
    return updated


def _do_generate_key(state):
    LOGGER.debug("KEY GENERATION")

    digital_signature = BGXCrypto.DigitalSignature()
    private_key = digital_signature.getSigningKey()
    LOGGER.debug("New private key generated: " + str(private_key))

    updated = {k: v for k, v in state.items()}
    return updated


def _do_init(full_name, private_key, ethereum_address, state):
    #msg = 'Setting "{n}" to {v}'.format(n=name, v=value)
    #LOGGER.debug(msg)

    #if name in state:
    #    raise InvalidTransaction(
    #        'Verb is "init", but already exists: Name: {n}, Value {v}'.format(
    #            n=name,
    #            v=state[name]))

    updated = {k: v for k, v in state.items()}
    #updated[name] = value

    #if full_name == "transfer":
    #    LOGGER.debug("WOW")

    ############################LOGGER.debug("############################################################################")
    ############################LOGGER.debug("############################################################################")

    LOGGER.debug("Info from sonsole: full_name - " + str(full_name))
    LOGGER.debug("Info from sonsole: private_key - " + str(private_key))
    LOGGER.debug("Info from sonsole: ethereum_address - " + str(ethereum_address))

    ############################ds = BGXCrypto.DigitalSignature(private_key)
    ############################msg = "Hello"
    ############################cipher = ds.sign(msg)
    ############################LOGGER.debug(str(cipher))
    ############################res = ds.verify(cipher, msg)
    ############################LOGGER.debug(str(res))

    ############################LOGGER.debug("############################################################################")
    ############################LOGGER.debug("############################################################################")
    
    LOGGER.debug("Emission - start")
    
    digital_signature = BGXCrypto.DigitalSignature(private_key)

    LOGGER.debug("DigitalSignature is ready")

    wallet_address = ethereum_address

    ############################digital_signature = BGXCrypto.DigitalSignature()

    emission_mechanism = EmissionMechanism()
    LOGGER.debug("EmissionMechanism is ready")

    dec_amount = BGXlistener.balanceOf(wallet_address)
    LOGGER.debug("DEC amount on a wallet " + wallet_address + " = " + str(dec_amount))
    bgt_price = 0

    unique_tokens = emission_mechanism.releaseTokens("BGX Token", "BGT", "id", digital_signature, 1, wallet_address, bgt_price)
    LOGGER.debug("Emission - ok")

    for token in unique_tokens:
        key = str(token.getId())
        value = str(token.toJSON())
        LOGGER.debug("New token: id " + str(key) + "  -  value " + str(value))
        lit_key = str(key[-2:])
        #updated[lit_key] = lit_key
        #updated[lit_key] = "123"
        ####updated[lit_key] = "1"
        updated[key] = value
    #updated[full_name] = "123"
    LOGGER.debug("Emission - end [%s]=updated=%s",full_name,updated)        
    return updated


def _do_inc(name, value, state):
    msg = 'Incrementing "{n}" by {v}'.format(n=name, v=value)
    LOGGER.debug(msg)

    if name not in state:
        raise InvalidTransaction(
            'Verb is "inc" but name "{}" not in state'.format(name))

    curr = state[name]
    incd = curr + value

    if incd > MAX_VALUE:
        raise InvalidTransaction(
            'Verb is "inc", but result would be greater than {}'.format(
                MAX_VALUE))

    updated = {k: v for k, v in state.items()}
    updated[name] = incd

    return updated


def _do_dec(name, value, state):
    msg = 'Decrementing "{n}" by {v}'.format(n=name, v=value)
    LOGGER.debug(msg)

    if name not in state:
        raise InvalidTransaction(
            'Verb is "dec" but name "{}" not in state'.format(name))

    curr = state[name]
    decd = curr - value

    if decd < MIN_VALUE:
        raise InvalidTransaction(
            'Verb is "dec", but result would be less than {}'.format(
                MIN_VALUE))

    updated = {k: v for k, v in state.items()}
    updated[name] = decd

    return updated
