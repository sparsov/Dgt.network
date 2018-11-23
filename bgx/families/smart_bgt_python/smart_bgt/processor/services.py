
# Copyright 2018 NTRlab (https://ntrlab.ru)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Mikhail Kashchenko


import logging
import sys
import json
from web3 import Web3, HTTPProvider
#from ecdsa import SigningKey, SECP256k1

LOGGER = logging.getLogger(__name__)

class BGXlistener:
    
    DECAir = '{}'
    DECOwn = '{}'
    def balanceOf(wallet_address):
        DEC_ADDRESS = "0xA442f92796E756dA0b8d4AA88552131A042A9d0E"
        CONTRACT_ADDRESS = "0x1046154E52152411f3DA880661B2E5E4a6fb86E8" #'0xa442f92796e756da0b8d4aa88552131a042a9d0e' # '0x11Ce8357fa42Dc336778381865a7ED1c76b38C4a'
        if BGXlistener.DECAir == '{}':
            with open('./DECAir.json') as file:
                #BGXlistener.DECAir = file.readlines()
                try:
                    decJson = json.load(file)
                    BGXlistener.DECAir = json.dumps(decJson)
                except:
                    LOGGER.debug('BGXlistener cant read json %s',sys.exc_info()[0])
                
            
        if BGXlistener.DECOwn == '{}':
            with open('./DEC.json') as file:
                try:
                    decJson = json.load(file)
                    BGXlistener.DECOwn = json.dumps(decJson)
                except:
                    LOGGER.debug('BGXlistener cant read json %s',sys.exc_info()[0])
            #LOGGER.debug('BGXlistener DECOwn=(%s)',BGXlistener.DECOwn)

        if True :
            # Connecting to test net ropsten through infura
            infura_provider = HTTPProvider('https://ropsten.infura.io')
            web3 = Web3(infura_provider)

            if not web3.isConnected():
                # raise something
                LOGGER.debug('WEB3 is not connected')
                return 0
            addr = DEC_ADDRESS
            LOGGER.debug('WEB3 GET CONTRACT=%s wallet_address=%s',CONTRACT_ADDRESS,wallet_address)
            #contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=DECAir ) #CONTRACT_INTERFACE)
            contract = web3.eth.contract(address=addr, abi=BGXlistener.DECOwn ) #CONTRACT_INTERFACE)
            LOGGER.debug('WEB3 contract=%s',contract)
            total = contract.functions.totalSupply().call()
            val = contract.functions.balanceOf(wallet_address).call()
            LOGGER.debug('WEB3 total=%s val=%s',total,val)
            return val
        else:
            return 0

# Namespace for logger function

class BGXlog:

    def logInfo(str):
        logging.info(str)

    def logError(str):
        logging.error(str)


# Namespace for general configuration

class BGXConf:

    DEFAULT_STORAGE_PATH = './'
    MAX_RETRY_CREATE_DB = 10

