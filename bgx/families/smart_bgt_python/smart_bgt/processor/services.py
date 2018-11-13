
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
import hashlib
#import ecdsa
from web3 import Web3, HTTPProvider

from sawtooth_signing.secp256k1 import Secp256k1Context as ecdsa


# Namespace for ethereum listener

class BGXlistener:

    CONTRACT_ADDRESS = '0x11Ce8357fa42Dc336778381865a7ED1c76b38C4a'
    CONTRACT_INTERFACE = '''[
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "name",
    		"outputs": [
    			{
    				"name": "",
    				"type": "string"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_spender",
    				"type": "address"
    			},
    			{
    				"name": "_value",
    				"type": "uint256"
    			}
    		],
    		"name": "approve",
    		"outputs": [
    			{
    				"name": "",
    				"type": "bool"
    			}
    		],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [],
    		"name": "pullTokens",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "totalSupply",
    		"outputs": [
    			{
    				"name": "",
    				"type": "uint256"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_from",
    				"type": "address"
    			},
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_amount",
    				"type": "uint256"
    			}
    		],
    		"name": "DECAirdropSend",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_from",
    				"type": "address"
    			},
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_value",
    				"type": "uint256"
    			}
    		],
    		"name": "transferFrom",
    		"outputs": [
    			{
    				"name": "",
    				"type": "bool"
    			}
    		],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_from",
    				"type": "address"
    			},
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_amount",
    				"type": "uint256"
    			}
    		],
    		"name": "DECAirdropSendToNode",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "decimals",
    		"outputs": [
    			{
    				"name": "",
    				"type": "uint8"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_amount",
    				"type": "uint256"
    			}
    		],
    		"name": "pushTokens",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "granularity",
    		"outputs": [
    			{
    				"name": "",
    				"type": "uint256"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_address",
    				"type": "address"
    			}
    		],
    		"name": "setDECAirdropContract",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_from",
    				"type": "address"
    			},
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_amount",
    				"type": "uint256"
    			},
    			{
    				"name": "_userData",
    				"type": "bytes"
    			},
    			{
    				"name": "_operatorData",
    				"type": "bytes"
    			}
    		],
    		"name": "operatorSend",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [
    			{
    				"name": "",
    				"type": "address"
    			}
    		],
    		"name": "balanceOf",
    		"outputs": [
    			{
    				"name": "",
    				"type": "uint256"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [],
    		"name": "renounceOwnership",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "owner",
    		"outputs": [
    			{
    				"name": "",
    				"type": "address"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "isOwner",
    		"outputs": [
    			{
    				"name": "",
    				"type": "bool"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_operator",
    				"type": "address"
    			}
    		],
    		"name": "authorizeOperator",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [],
    		"name": "symbol",
    		"outputs": [
    			{
    				"name": "",
    				"type": "string"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_amount",
    				"type": "uint256"
    			},
    			{
    				"name": "_userData",
    				"type": "bytes"
    			}
    		],
    		"name": "send",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_to",
    				"type": "address"
    			},
    			{
    				"name": "_value",
    				"type": "uint256"
    			}
    		],
    		"name": "transfer",
    		"outputs": [
    			{
    				"name": "",
    				"type": "bool"
    			}
    		],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_address",
    				"type": "address"
    			},
    			{
    				"name": "_amount",
    				"type": "uint256"
    			}
    		],
    		"name": "DECAirdropInit",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [
    			{
    				"name": "",
    				"type": "address"
    			},
    			{
    				"name": "",
    				"type": "address"
    			}
    		],
    		"name": "isOperatorFor",
    		"outputs": [
    			{
    				"name": "",
    				"type": "bool"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": true,
    		"inputs": [
    			{
    				"name": "_owner",
    				"type": "address"
    			},
    			{
    				"name": "_spender",
    				"type": "address"
    			}
    		],
    		"name": "allowance",
    		"outputs": [
    			{
    				"name": "_amount",
    				"type": "uint256"
    			}
    		],
    		"payable": false,
    		"stateMutability": "view",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "newOwner",
    				"type": "address"
    			}
    		],
    		"name": "transferOwnership",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"constant": false,
    		"inputs": [
    			{
    				"name": "_operator",
    				"type": "address"
    			}
    		],
    		"name": "revokeOperator",
    		"outputs": [],
    		"payable": false,
    		"stateMutability": "nonpayable",
    		"type": "function"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "from",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "to",
    				"type": "address"
    			},
    			{
    				"indexed": false,
    				"name": "value",
    				"type": "uint256"
    			}
    		],
    		"name": "Transfer",
    		"type": "event"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "operator",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "from",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "to",
    				"type": "address"
    			},
    			{
    				"indexed": false,
    				"name": "amount",
    				"type": "uint256"
    			},
    			{
    				"indexed": false,
    				"name": "userData",
    				"type": "bytes"
    			},
    			{
    				"indexed": false,
    				"name": "operatorData",
    				"type": "bytes"
    			}
    		],
    		"name": "Sent",
    		"type": "event"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "operator",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "tokenHolder",
    				"type": "address"
    			}
    		],
    		"name": "AuthorizedOperator",
    		"type": "event"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "operator",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "tokenHolder",
    				"type": "address"
    			}
    		],
    		"name": "RevokedOperator",
    		"type": "event"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "owner",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "spender",
    				"type": "address"
    			},
    			{
    				"indexed": false,
    				"name": "value",
    				"type": "uint256"
    			}
    		],
    		"name": "Approval",
    		"type": "event"
    	},
    	{
    		"anonymous": false,
    		"inputs": [
    			{
    				"indexed": true,
    				"name": "previousOwner",
    				"type": "address"
    			},
    			{
    				"indexed": true,
    				"name": "newOwner",
    				"type": "address"
    			}
    		],
    		"name": "OwnershipTransferred",
    		"type": "event"
    	}
    ]'''

    def balanceOf(wallet_address):
        # Connecting to test net ropsten through infura
        infura_provider = HTTPProvider('https://ropsten.infura.io')
        web3 = Web3(infura_provider)

        if not web3.isConnected():
            # raise something
            return False

        contract = web3.eth.contract(address=BGXlistener.CONTRACT_ADDRESS, abi=BGXlistener.CONTRACT_INTERFACE)
        return contract.functions.balanceOf(wallet_address).call()


# Namespace for logger function

class BGXlog:

    def logInfo(str):
        logging.info(str)

    def logError(str):
        logging.error(str)


# Namespace for cryptofunction

class BGXCrypto:

    def strHash(str):
        return hashlib.sha256(str.encode('utf-8')).hexdigest()

    def intHash(str):
        return int(BGXCrypto.strHash(str), 16)

    class DigitalSignature:

        def __init__(self, verifying_key=None):
            if verifying_key is None:
                self._context = ecdsa.Secp256k1Context()
                self._signing_key = self._context.new_random_private_key()
                self._verifying_key = self._context.get_public_key(self._signing_key)
            else:
                self._signing_key = None
                self._verifying_key = verifying_key

        def sign(self, message):
            if self._signing_key is None:
                BGXlog.logError('Fail! Can not sign this')
                # raise something
                return False
            return self._context.sign(message, self._signing_key)

        def verify(self, sign, message):
            return self._context.verify(sign, message, self._verifying_key)

        def getVerifyingKey(self):
            return self._verifying_key

        #def __init__(self, verifying_key=None):
        #    if verifying_key is None:
        #        self._signing_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
        #        self._verifying_key = self._signing_key.get_verifying_key()
        #    else:
        #        self._signing_key = None
        #        self._verifying_key = verifying_key

        #def sign(self, message):
        #    if self._signing_key is None:
        #        BGXlog.logError('Fail! Can not sign this')
        #        # raise something
        #        return False
        #    return self._signing_key.sign(str(message).encode('utf-8'))

        #def verify(self, sign, message):
        #    return self._verifying_key.verify(sign, str(message).encode('utf-8'))

        #def getVerifyingKey(self):
        #    return self._verifying_key


# Namespace for general configuration

class BGXConf:

    DEFAULT_STORAGE_PATH = './'
    MAX_RETRY_CREATE_DB = 10
    #LOGGER = logging.getLogger(__name__)
    FAMILY_NAME = 'smart-bgt'
    FAMILY_VER  = '1.0'
    SMART_BGT_ADDRESS_PREFIX = hashlib.sha512(FAMILY_NAME.encode('utf-8')).hexdigest()[0:6]

    def make_smart_bgt_address(name):
        return SMART_BGT_ADDRESS_PREFIX + hashlib.sha512(name.encode('utf-8')).hexdigest()[-64:]
