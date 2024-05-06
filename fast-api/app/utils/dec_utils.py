#from fastapi import APIRouter
#from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
#import app.messaging.error_handlers as error_handlers
#import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token



async def get_dec_emission_key(query: QueryValidatorHandler):
    address = get_full_addr(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)
    LOGGER.debug('Request get_dec_emission_key addr={}'.format(address))                     
    response = await query.get_state_by_addr(address=address)                                                                                            
    #LOGGER.debug('response={}'.format(response))                 
    dec = loads_dec_token(response['value'],DEC_EMISSION_KEY)
    return dec, response  
   

