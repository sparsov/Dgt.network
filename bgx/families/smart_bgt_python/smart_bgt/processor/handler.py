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
from smart_bgt.processor.services import BGXlistener
from smart_bgt.processor.crypto import BGXCrypto
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

def sha512(data):
    return hashlib.sha512(data).hexdigest()

def get_prefix(self):
    return sha512(FAMILY_NAME.encode('utf-8'))[0:6]

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
        verb, args = _unpack_transaction(transaction)
        LOGGER.info('SmartBgtTransactionHandler verb=%s args %s',verb,args)
        try:
 
            if verb == 'init':
                private_key = args['private_key']
                digital_signature = BGXCrypto.DigitalSignature(private_key)
                open_key = digital_signature.getVerifyingKey()
                state = _get_state_data([args['Name'], open_key], context)
            else:
                state = _get_state_data([args['Name'],args['to_addr']] if verb == 'transfer' else [args['Name'], 'SHIT'], context)
            LOGGER.info('SmartBgtTransactionHaEmissionMechanismndler _do_smart_bgt ')
            updated_state = _do_smart_bgt(verb, args, state)

            _set_state_data(updated_state, context)
        except AttributeError:
            raise InvalidTransaction('Args are required')

def _unpack_transaction(transaction):
    return  _decode_transaction(transaction)

    #_validate_verb(verb)
    #_validate_name(name)
    #_validate_value(value)

    #return verb, name, value, value_2


def _decode_transaction(transaction):
    try:
        content = cbor.loads(transaction.payload)
    except:
        raise InvalidTransaction('Invalid payload serialization')

    try:
        verb = content['Verb']
    except AttributeError:
        raise InvalidTransaction('Verb is required')
    """
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
    """
    return verb, content # name, value, value_2


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


def _get_state_data(names, context):
    alist = []
    for name  in names:
        address = make_smart_bgt_address(name)
        alist.append(address)
    state_entries = context.get_state(alist)

    LOGGER.debug('_get_state_data state_entries=%s',state_entries)
    try:
        states = {}
        for entry  in state_entries:
            state = cbor.loads(entry.data)
            for key,val in state.items():
                LOGGER.debug('_get_state_data add=%s',key)
                states[key] = val
        return states #cbor.loads(state_entries[0].data)
    except IndexError:
        return {}
    except:
        raise InternalError('Failed to load state data')


def _set_state_data( state, context):
    new_states = {}
    for key,val in state.items():
        LOGGER.debug('_set_state_data  [%s]=%s',key,val)
        address = make_smart_bgt_address(key)
        encoded = cbor.dumps({key:val})
        new_states[address] = encoded

    addresses = context.set_state(new_states)

    if not addresses:
        LOGGER.debug('_set_state_data  State error')
        raise InternalError('State error')
    LOGGER.debug('_set_state_data  DONE address=%s',address)

def _do_smart_bgt(verb, args, state):
    verbs = {
        'set': _do_set,
        'inc': _do_inc,
        'dec': _do_dec,
        'transfer' : _do_transfer
    }
    LOGGER.debug('_do_smart_bgt request verb=%s',verb)

    if verb == 'init':
        return _do_init(args, state)

    if 'Name' not in args:
        return _do_generate_key(state)
    try:
        return verbs[verb](args, state)
    except KeyError:
        # This would be a programming error.
        raise InternalError('Unhandled verb: {}'.format(verb))


def _do_set(args, state):
    name  = args['Name']
    value = args['Value']
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


def _do_init(args,state):
    #msg = 'Setting "{n}" to {v}'.format(n=name, v=value)
    #LOGGER.debug(msg)

    #if name in state:
    #    raise InvalidTransaction(
    #        'Verb is "init", but already exists: Name: {n}, Value {v}'.format(
    #            n=name,
    #            v=state[name]))
    LOGGER.debug("_do_init ...")
    try:
        full_name  = args['Name']
        private_key = args['private_key']
        ethereum_address = args['ethereum_address']
        num_bgt =  int(args['num_bgt'])
        bgt_price = float(args['bgt_price'])
        dec_price = float(args['dec_price'])
    except KeyError:
        LOGGER.debug("_do_init not all arg")

    LOGGER.debug("have state=%s",state)

    updated = {k: v for k, v in state.items()}
    
    LOGGER.debug("Emission - start")
    
    digital_signature = BGXCrypto.DigitalSignature(private_key)
    wallet_address = ethereum_address

    emission_mechanism = EmissionMechanism()
    dec_amount = BGXlistener.balanceOf(wallet_address)

    #unique_tokens = emission_mechanism.releaseTokens("BGX Token", "BGT", "id", digital_signature, 1, wallet_address, bgt_price)
    token, meta = emission_mechanism.releaseTokens(full_name, digital_signature, ethereum_address, num_bgt, \
                                                   bgt_price, dec_price)
    LOGGER.debug("Emission - ready")

    if token is None or meta is None:
        LOGGER.debug("Emission failed: not enough money")
        return updated
    
    key = str(token.getOwnerKey()) + str(token.getGroupId())
    LOGGER.debug("KEY:" + key)
    value = str(token.toJSON())
    LOGGER.debug("VALUE:" + value)


    updated[full_name] = str(meta.toJSON()) ############# updated[full_name] = {'val': num_bgt,'group' : 'BGT'}
    open_key = digital_signature.getVerifyingKey()
    updated[open_key] = str(token.toJSON())


    LOGGER.debug("Emission - end updated=%s",updated)        
    return updated


def _do_transfer(args,state):
    LOGGER.debug("_do_transfer ...")
    try:
        from_addr = args['Name']
        to_addr   = args['to_addr']
        num_bgt =  float(args['num_bgt'])
    except KeyError:
        LOGGER.debug("_do_transfer not all arg")

    LOGGER.debug("have state=%s",state)
    if from_addr not in state:
        LOGGER.debug("SET ADDR FROM")
        raise InvalidTransaction('Verb is "transfer" but name "{}" not in state'.format(from_addr))

    from_token_str = state[from_addr] #token
    to_token_str = state[to_addr] if to_addr in state else None #token1
    LOGGER.debug("TRANSFER from %s->%s",from_addr,to_addr)
    LOGGER.debug("TRANSFER from %s->%s", from_token_str, to_token_str)

    from_token = Token()
    LOGGER.debug("Token ready")
    from_token.fromJSON(from_token_str)
    LOGGER.debug("From token: %s", str(from_token.toJSON()))

    to_token = Token()
    if to_token_str is None:
        to_token.copy(from_token, to_addr)
    else:
        to_token.fromJSON(to_token_str)
    LOGGER.debug("To token: %s", str(to_token.toJSON()))

    res = from_token.send(to_token, float(num_bgt))
    LOGGER.debug("RESULT of transfer: %s", str(res))

    updated = {k: v for k, v in state.items()}

    if res:
        #updated[name] = value
        #LOGGER.debug("have state=%s",updated)
        LOGGER.debug("WOW")
        updated[from_addr] = from_token.toJSON()
        updated[to_addr] = to_token.toJSON()
        #########token['val'] = token['val'] - num_bgt # send tokens to ethereum_address
        #########updated[from_addr] = token
        #########updated[to_addr] = {'val':  token1['val'] + num_bgt if token1 else num_bgt,'group' : 'BGT'}
    LOGGER.debug("Transfer - end updated=%s",updated)
    return updated


def _do_inc(args, state):
    name  = args['Name']
    value = args['Value']
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


def _do_dec(args, state):
    name  = args['Name']
    value = args['Value']
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
