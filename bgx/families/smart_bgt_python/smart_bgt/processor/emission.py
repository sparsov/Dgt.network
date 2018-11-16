
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


import time
#import services
#import inspect

from smart_bgt.processor.services import BGXCrypto, BGXlistener
from smart_bgt.processor.token import Token


# Prototype for a EmissionMechanism class
# without check of ethereum account

class EmissionMechanism:

    def __init__(self):
        self.type = "BGX"

    # TODO: implement

    def checkEthereum(self, bgt_amount, wallet_address):
        dec_amount = int(BGXlistener.balanceOf(wallet_address)) 
        return int(bgt_amount) * 0 <= dec_amount

    # TODO: implement

    def getProvedHashOfClass(self):
        return True

    # TODO: implement

    def checkHashOfClass(self):
        #lines = inspect.getsource(EmissionMechanism)
        #hash = BGXCrypto.intHash(lines)
        return True

    def releaseTokens(self, name, symbol, company_id, signing_key, tokens_amount, wallet_address, bgt_price):
        #services.BGXlog.logInfo('Emission in progress')
        #seed = str(time.time())
        seed = ""
        imprint = name + symbol + company_id + seed
        group_code = str(BGXCrypto.intHash(imprint))

        dec_amount = BGXlistener.balanceOf(wallet_address)
        if tokens_amount * bgt_price > dec_amount:
            return False

        tokens = []
        for tokenNumber in range(tokens_amount):
            token = Token(name, symbol, company_id, group_code, signing_key, tokenNumber)
            #token = Token("BGX Token", "BGT", "id", "code", 1, signing_key, tokenNumber)
            tokens.append(token)

        return tokens


#digital_signature = services.BGXCrypto.DigitalSignature()
#wallet_address = '0xD5779261bC3F08F13E6D520CD28E6A3FE5F47B8B'
#unique_tokens = EmissionMechanism.releaseTokens("BGX Token", "BGT", "id", 1, digital_signature, 10, wallet_address)
#for token in unique_tokens:
#     print(token.verifyToken(digital_signature))