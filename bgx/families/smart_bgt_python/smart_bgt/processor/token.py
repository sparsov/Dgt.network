

from smart_bgt.processor.crypto import BGXCrypto
import math
import json
import logging
from smart_bgt.processor.utils  import SMART_BGT_CREATOR_KEY
BASIC_DECIMALS = 18


class MetaToken:

    def __init__(self, name, symbol, company_id, group_code, total_supply, description, internal_token_price, \
                 digital_signature):
        ##########BGXlog.logInfo("Init metatoken")
        if not self.__checkValues(total_supply, internal_token_price, digital_signature):
            ##########BGXlog.logInfo("Init metatoken - Error")
            # raise something
            return False

        self.name = name
        self.symbol = symbol
        self.company_id = company_id
        self.group_code = group_code
        self.total_supply = total_supply
        self.granularity = 1
        # max value of token = 1000000000000000000 = 10^18
        # max int in python  = 9223372036854775807
        self.decimals = BASIC_DECIMALS
        self.description = description
        # USD by default
        self.currency_code = 1
        self.internal_token_price = internal_token_price
        self.bgx_conversion = False
        self.internal_conversion = False
        self.ethereum_conversion = False
        self.owner_key = digital_signature.getVerifyingKey()
        ##########BGXlog.logInfo("Init metatoken - Ready")

    def __checkValues(self, total_supply, internal_token_price, digital_signature):
        if not isinstance(total_supply, int):
            ##########BGXlog.logError("Not integer : total_supply" )
            return False
        if not isinstance(internal_token_price, int):
            ##########BGXlog.logError("Not integer : internal_token_price" )
            return False
        if not isinstance(digital_signature, BGXCrypto.DigitalSignature):
            ##########BGXlog.logError("Bad digital signature")
            return False
        return True

    def toJSON(self):
        data = {'name': self.name, 'total_supply': str(self.total_supply), 'granularity': str(self.granularity), \
                'decimals': str(self.decimals), SMART_BGT_CREATOR_KEY: self.owner_key, 'group_code': self.group_code}
        return json.dumps(data)

# Prototype for a Token class.
# Note: must be JSON-serializable

class Token:

    def __init__(self, group_code = None, balance = 0, digital_signature = None, granularity = 1, decimals = 18):
        ##########BGXlog.logInfo("Init token")
        if group_code == None:
            self.active_flag = False
            self.group_code = 'None'
            self.balance = 0
            self.granularity = granularity
            self.decimals = decimals
            self.owner_key = 'None'
            self.sign = 'None'
        else:
            if not self.__checkValues(balance, granularity, decimals, digital_signature):
                ##########BGXlog.logInfo("Init token - Error")
                # raise something
                return False

            self.active_flag = True
            self.group_code = str(group_code)
            self.balance = balance
            self.granularity = granularity
            self.decimals = decimals
            self.owner_key = str(digital_signature.getVerifyingKey())
            self.sign = str(digital_signature.sign(self.getImprint()))

    def __str__(self):
        return self.getImprint()

    def copy(self, token, owner_key):
        self.active_flag = True
        self.group_code = token.getGroupId()
        self.owner_key = owner_key

    def __checkValues(self, balance, granularity, decimals, digital_signature=None):
        if not isinstance(balance, int) or balance < 0:
            ##########BGXlog.logError("Bad integer : balance" )
            return False
        if not isinstance(granularity, int) or granularity < 0:
            ##########BGXlog.logError("Bad integer : balance" )
            return False
        if not isinstance(decimals, int) or decimals < 0:
            ##########BGXlog.logError("Bad integer : balance" )
            return False
        if digital_signature is not None and not isinstance(digital_signature, BGXCrypto.DigitalSignature):
            ##########BGXlog.logError("Bad digital signature")
            return False
        return True

    def getGroupId(self):
        return self.group_code

    def getOwnerKey(self):
        return self.owner_key

    def verifyToken(self, digital_signature):
        return digital_signature.verify(self.sign, self.getImprint())

    def getSign(self):
        return self.sign

    def getImprint(self):
        imprint = self.group_code + str(self.balance) + str(self.granularity) + \
                  str(self.decimals) + self.owner_key
        return imprint

    def toJSON(self):
        data = {'group_code': str(self.group_code), 'granularity': str(self.granularity), 'balance': str(self.balance),\
                'decimals': str(self.decimals), 'owner_key': str(self.owner_key), 'sign': str(self.sign)}
        return json.dumps(data)

    def fromJSON(self, json_string):
        data = json.loads(json_string)
        group_code = data['group_code']
        balance = int(data['balance'])
        granularity = int(data['granularity'])
        decimals = int(data['decimals'])
        owner_key = data['owner_key']
        sign = data['sign']

        if not self.__checkValues(balance, granularity, decimals):
            ##########BGXlog.logInfo("Loading token - Error")
            # raise something
            return False

        if not self.active_flag:
            msg = 'Update "{n}"'.format(n=self.toJSON())
            ##########BGXlog.logInfo(msg)

        self.active_flag = True
        self.group_code = group_code
        self.balance = balance
        self.granularity = granularity
        self.decimals = decimals
        self.owner_key = owner_key
        self.sign = sign

        ###############3if not self.verifyToken():
            ###################msg = 'Failed load from "{n}"'.format(n=self.toJSON())
            ##########BGXlog.logError(msg)
            # raise something
            ####################return False

    def getBalance(self):
        return self.balance

    def __setBalance(self, balance):
        self.balance = balance

    def getDecimals(self):
        return self.decimals

    def __setDecimals(self, decimals):
        self.decimals = decimals

    def __intToIternalFormat(self, amount):
        if amount <= 0:
            return BASIC_DECIMALS, 0

        decimals = 0
        flag = amount / 10
        while int(flag) == flag:
            amount /= 10
            flag /= 10
            decimals += 1

        return decimals, int(amount)

    def send(self, to_token, amount = 0):
        if  not isinstance(to_token, Token) or (not isinstance(amount, float) and \
            not isinstance(amount, int)) or amount <= 0 or pow(10, BASIC_DECIMALS) * amount < 1:
            ##########BGXlog.logInfo(Send error - bad parameters)
            return False
        from_decimals = self.getDecimals()
        from_balance = self.getBalance()

        to_decimals = to_token.getDecimals()
        to_balance = to_token.getBalance()

        from_amount = from_balance * pow(10, from_decimals)
        to_amount = to_balance * pow(10, to_decimals)
        send_amount = int(amount * pow(10, BASIC_DECIMALS))

        if from_amount < send_amount:
            ##########BGXlog.logInfo(Send error - not enough money)
            return False

        from_amount -= send_amount
        to_amount += send_amount
        from_decimals, from_balance = self.__intToIternalFormat(from_amount)
        to_decimals, to_balance = self.__intToIternalFormat(to_amount)

        self.__setDecimals(from_decimals)
        self.__setBalance(from_balance)
        to_token.__setDecimals(to_decimals)
        to_token.__setBalance(to_balance)
        return True
