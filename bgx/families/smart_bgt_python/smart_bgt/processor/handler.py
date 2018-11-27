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
import json


from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from smart_bgt.processor.utils  import FAMILY_NAME,FAMILY_VER,make_smart_bgt_address,SMART_BGT_ADDRESS_PREFIX
from smart_bgt.processor.services import BGXlistener
from smart_bgt.processor.crypto import BGXCrypto
from smart_bgt.processor.token import Token
from smart_bgt.processor.emission import EmissionMechanism


LOGGER = logging.getLogger(__name__)


def sha512(data):
    return hashlib.sha512(data).hexdigest()

def get_prefix():
    return sha512(FAMILY_NAME.encode('utf-8'))[0:6]

class BGXwallet():
    def __init__(self, public_key=None):
        self._public_key = public_key
        self._tokens = {}

    def append(self, token):
        if not isinstance(token, Token):
            #raise something
            return False
        key = token.getGroupId()
        self._tokens[key] = token.toJSON()

    def get_token(self, token_id):
        if token_id not in self._tokens:
            max_token = Token()
            cur_token = Token()
            for token_id in self._tokens.keys():
                token_str = self._tokens[token_id]
                cur_token.fromJSON(token_str)
                if max_token.getBalance() < cur_token.getBalance():
                    max_token = cur_token
            return max_token
            #return None
        else:
            token_str = self._tokens[token_id]
            del self._tokens[token_id]
            token = Token()
            token.fromJSON(token_str)
            return token

    def toJSON(self):
        return json.dumps(self._tokens)

    def fromJSON(self, json_string):
        data = json.loads(json_string)
        self._tokens = {}
        for k, v in data.items():
            self._tokens[k] = v


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
        LOGGER.info('SmartBgtTransactionHandler verb=%s args %s', verb, args)
        try:
            if verb == 'init':
                private_key = args['private_key']
                digital_signature = BGXCrypto.DigitalSignature(private_key)
                open_key = digital_signature.getVerifyingKey()
                state = _get_state_data([args['Name'], open_key], context)
            elif verb == 'transfer':
                state = _get_state_data([args['Name'], args['to_addr']], context)
            else:
                state = _get_state_data([args['Name']], context)

            LOGGER.info('SmartBgtTransactionHaEmissionMechanismndler _do_smart_bgt ')
            updated_state = _do_smart_bgt(verb, args, state)
            _set_state_data(updated_state, context)
        except AttributeError:
            raise InvalidTransaction('Args are required')


def _unpack_transaction(transaction):
    return  _decode_transaction(transaction)


def _decode_transaction(transaction):
    try:
        content = cbor.loads(transaction.payload)
    except:
        raise InvalidTransaction('Invalid payload serialization')
    try:
        verb = content['Verb']
    except AttributeError:
        raise InvalidTransaction('Verb is required')

    return verb, content


def _get_state_data(names, context):
    alist = []
    for name in names:
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
        return states
    except IndexError:
        return {}
    except:
        raise InternalError('Failed to load state data')


def _set_state_data(state, context):
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
    LOGGER.debug('_do_smart_bgt request verb=%s',verb)

    try:
        if verb == 'init':
            return _do_init(args, state)
        elif verb == 'generate_key':
            return _do_generate_key(state)
        elif verb == 'transfer':
            return _do_transfer(args, state)
    except KeyError:
        # This would be a programming error.
        raise InternalError('Unhandled verb: {}'.format(verb))


def _do_generate_key(state):
    LOGGER.debug("KEY GENERATION")

    digital_signature = BGXCrypto.DigitalSignature()
    private_key = digital_signature.getSigningKey()
    LOGGER.debug("New private key generated: " + str(private_key))

    updated = {k: v for k, v in state.items()}
    return updated


def _do_init(args,state):
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
    emission_mechanism = EmissionMechanism()
    token, meta = emission_mechanism.releaseTokens(full_name, digital_signature, ethereum_address, num_bgt, \
                                                   bgt_price, dec_price)
    LOGGER.debug("Emission - ready")

    if token is None or meta is None:
        LOGGER.debug("Emission failed: not enough money")
        return updated

    updated[full_name] = str(meta.toJSON())

    open_key = digital_signature.getVerifyingKey()
    wallet = BGXwallet(open_key)
    wallet.append(token)
    updated[open_key] = str(wallet.toJSON())

    LOGGER.debug("Emission - end updated=%s",updated)        
    return updated


def _do_transfer(args,state):
    LOGGER.debug("_do_transfer ...")
    try:
        from_addr = args['Name']
        to_addr   = args['to_addr']
        num_bgt =  float(args['num_bgt'])
        group_id = args['group_id']
    except KeyError:
        LOGGER.debug("_do_transfer not all arg")

    LOGGER.debug("have state=%s",state)
    if from_addr not in state:
        LOGGER.debug("SET ADDR FROM")
        raise InvalidTransaction('Verb is "transfer" but name "{}" not in state'.format(from_addr))

    LOGGER.debug("TRANSFER from %s->%s", from_addr, to_addr)

    from_wallet_str = state[from_addr]
    from_wallet = BGXwallet()
    from_wallet.fromJSON(from_wallet_str)
    from_token = from_wallet.get_token(group_id)
    LOGGER.debug("From token: %s", str(from_token.toJSON()))

    to_token = Token()
    to_wallet = BGXwallet()
    if to_addr in state:
        to_wallet_str = state[to_addr]
        to_wallet.fromJSON(to_wallet_str)
        to_token = to_wallet.get_token(group_id)
    #to_token_str = state[to_addr] if to_addr in state else None
    LOGGER.debug("To token: %s", str(to_token.toJSON()))

    res = from_token.send(to_token, float(num_bgt))
    LOGGER.debug("RESULT of transfer: %s", str(res))

    updated = {k: v for k, v in state.items()}

    if res:
        from_wallet.append(from_token)
        to_wallet.append(to_token)
        updated[from_addr] = from_wallet.toJSON()
        updated[to_addr] = to_wallet.toJSON()

    LOGGER.debug("Transfer - end updated=%s",updated)
    return updated
