# Copyright 2016, 2017 DGT NETWORK INC © Stanislav Parsov
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

import base64
import hashlib
import random
import time
from datetime import datetime
from dgt_signing import CryptoFactory,create_context
"""
from smart_bgt.processor.utils import FAMILY_NAME as SMART_BGX_FAMILY
from smart_bgt.processor.utils import FAMILY_VER as SMART_BGX_VER
from smart_bgt.processor.utils import SMART_BGT_META,SMART_BGT_CREATOR_KEY,SMART_BGT_PRESENT_AMOUNT
from smart_bgt.processor.utils import make_smart_bgt_address
# bgt families                                                                               
from dgt_bgt.client_cli.generate import BgtPayload,create_bgt_transaction,loads_bgt_token    
from dgt_bgt.processor.handler import make_bgt_address, make_bgt_prefix 
"""
from app.utils.logger import logger as LOGGER


def _sha512(data):
    return hashlib.sha512(data).hexdigest()

def _base64url2public(addr):
    try:
        return base64.urlsafe_b64decode(addr).decode("utf-8") 
    except :
        raise errors.BadWalletAddress()
        

def _public2base64url(key):
    return base64.urlsafe_b64encode(key.encode()).decode('utf-8')


_context = create_context('secp256k1')                                         
_private_key = _context.new_random_private_key()                          
_public_key = _context.get_public_key(_private_key)                  
_crypto_factory = CryptoFactory(_context)                                 
signer = _crypto_factory.new_signer(_private_key)                   
LOGGER.debug(' _signer PUBLIC_KEY=%s',_public_key.as_hex()[:8])








