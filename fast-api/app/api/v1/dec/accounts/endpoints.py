from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse,DgtResponse, AccountCreate, DgtPagingListResponse, DgtPagingDictResponse
from app.utils.dec_utils import get_dec_accounts,get_dec_aliases, get_dec_account_by_id, get_dec_alias_by_id
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token

router = APIRouter()



@router.get("/accounts",response_model=DgtPagingDictResponse)
async def get_accounts(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # dec show _DEC_EMISSION_KEY_
    dec, response = await get_dec_accounts(request,query)
    paging_controls = query._get_paging_controls(request) 
    return query._wrap_paginated_response(                                                           
        request=request,                                                                            
        response=response,                                                                          
        controls=paging_controls,                                                                   
        data=dec)
                  

@router.get("/accounts/{account_id}/parameters",response_model=DgtResponse)                                                                      
async def get_account_params(request: Request,account_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    wallet, response = await get_dec_account_by_id(request,account_id,query)
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=wallet,                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            
                                                                            

@router.get("/accounts/{account_id}/balance",response_model=DgtResponse)                                                                      
async def get_account_balance(request: Request,account_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    wallet, response = await get_dec_account_by_id(request,account_id,query)                                                                     
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={DEC_TOTAL_SUM : wallet[DEC_TOTAL_SUM]},                                                                                                       
        metadata=query._get_metadata(request, response))

@router.get("/accounts/{account_id}/info",response_model=DgtResponse)                                                                      
async def get_account_info(request: Request,account_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    """
    """    
    wallet, response = await get_dec_account_by_id(request,account_id,query)                                                                     
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=wallet,                                                                                                       
        metadata=query._get_metadata(request, response))

@router.post("/accounts/create",response_model=DgtResponse)                                                                      
async def post_create_account(request: Request,account: AccountCreate,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    LOGGER.debug('request account={}'.format(account)) 
    
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={},                                                                                                       
        metadata=query._get_metadata(request, None))


@router.get("/accounts/{alias}/info",response_model=DgtResponse)                                                                      
async def get_account_by_alias(request: Request,alias: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    dec, response = await get_dec_emission_key(query)                                                                     
    keys = dec[DEC_EMISSION_INFO][DATTR_VAL]
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=keys,                                                                                                       
        metadata=query._get_metadata(request, response))



@router.get("/accounts/aliases",response_model=DgtResponse)                                                                      
async def get_aliases(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    aliases, response = await get_dec_aliases(request,query)                     
                                                                              
    return query._wrap_response(                                              
        request,                                                              
        data=aliases,                                                             
        metadata=query._get_metadata(request, response))                      


@router.get("/accounts/aliases/{alias_id}/info",response_model=DgtResponse)                                                                      
async def get_alias_by_id(request: Request,alias_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    alias, response = await get_dec_alias_by_id(request,alias_id,query)            
                                                                                        
    return query._wrap_response(                                                        
        request,                                                                        
        data=alias,                                                                    
        metadata=query._get_metadata(request, response))                                



@router.post("/accounts/{account_id}/aliases",response_model=DgtResponse)                                                                      
async def post_add_alias(request: Request,account_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    dec, response = await get_dec_emission_key(query)
    supply = {}
    for attr in [DEC_TOTAL_SUM,DEC_MINTING_TOTAL,DEC_MINTING_REST,DEC_СORPORATE_TOTAL,DEC_СORPORATE_REST,DEC_SALE_TOTAL,DEC_SALE_REST]:
        supply[attr] = dec[attr] if not isinstance(dec[attr],dict) else dec[attr][DATTR_VAL]                                                                 

    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=supply,                                                                                                       
        metadata=query._get_metadata(request, response))





