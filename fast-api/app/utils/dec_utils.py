#from fastapi import APIRouter
from fastapi import Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
#import app.messaging.error_handlers as error_handlers
#import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token, _get_full_prefix, loads_dec_entries



async def get_dec_emission_key(query: QueryValidatorHandler):
    address = get_full_addr(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)
    LOGGER.debug('Request get_dec_emission_key addr={}'.format(address))                     
    response = await query.get_state_by_addr(address=address)                                                                                            
    #LOGGER.debug('response={}'.format(response))                 
    dec = loads_dec_token(response['value'],DEC_EMISSION_KEY)
    return dec, response  
   

async def get_dec_entries(request: Request,address: str,query: QueryValidatorHandler):
    
    LOGGER.debug('Request get_dec_entries addr={}'.format(address))                     
    response = await query.get_states_by_addr(request,address)                                                                                            
    #LOGGER.debug('response={}'.format(response))  
    entries = loads_dec_entries(response['entries'])
    return entries, response  


async def get_dec_accounts(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_WALLET_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)
   
    return entries, response  

async def get_dec_account_by_id(request: Request,account_id: str,query: QueryValidatorHandler):
    address = get_full_addr(account_id,DEC_WALLET_GRP,DEFAULT_DID)
    response = await query.get_state_by_addr(address=address)
    wallet = loads_dec_token(response['value'],account_id)
    
   
    return wallet, response  



async def get_dec_aliases(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_SYNONYMS_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)

    return entries, response  

async def get_dec_alias_by_id(request: Request,alias_id: str,query: QueryValidatorHandler):
    address = get_full_addr(alias_id,DEC_SYNONYMS_GRP,DEFAULT_DID)
    response = await query.get_state_by_addr(address=address)
    alias = loads_dec_token(response['value'],alias_id)


    return alias, response  


async def get_dec_assets(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_TARGET_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)
   
    return entries, response 



