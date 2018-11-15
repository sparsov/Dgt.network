

from smart_bgt.processor.services import BGXCrypto
import json


# Prototype for a Token class.
# Note: must be JSON-serializable

class Token:

    def __init__(self, name, symbol, company_id, group_code, digital_signature, seed = 0):
        #services.BGXlog.logInfo('Producing token')
        self.name = name
        self.symbol = symbol
        self.company_id = company_id
        self.group_code = group_code
        self.granularity = 1
        self.decimals = 18
        self.owner_key = digital_signature.getVerifyingKey()

        #if not isinstance(digital_signature, BGXCrypto.DigitalSignature):
            #services.BGXlog.logError('Wrong digital signature class as input in token creation')
            #raise something
            #return False

        imprint = name + symbol + company_id + group_code
        self.token_id = BGXCrypto.intHash(imprint + str(seed))
        self.sign = str(digital_signature.sign(self.getImprint()))

    def __str__(self):
        return self.getImprint()

    def verifyToken(self, digital_signature):
        return digital_signature.verify(self.sign, self.getImprint())

    def getSign(self):
        return self.sign

    def getImprint(self):
        imprint = self.name + self.symbol + self.company_id + self.group_code + str(self.token_id) + str(self.owner_key)
        return imprint

    def getId(self):
        return str(self.token_id)

    def toJSON(self):
        data = {'group_code': str(self.group_code), 'owner_key': self.owner_key, 'sign': self.sign}
        return str(json.dumps(data))

    # TODO: implement

    def fromJSON(self, data):
        return True