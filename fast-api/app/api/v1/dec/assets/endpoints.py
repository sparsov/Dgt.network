from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse,DgtResponse,DgtPagingDictResponse
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token
from app.utils.dec_utils import get_dec_assets
router = APIRouter()



@router.get("/assets/list",response_model=DgtPagingDictResponse)
async def get_assets(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # dec show _DEC_EMISSION_KEY_
    assets, response = await get_dec_assets(request,query)
    paging_controls = query._get_paging_controls(request)  
    return query._wrap_paginated_response(                                                           
        request=request,                                                                            
        response=response,                                                                          
        controls=paging_controls,                                                                   
        data=assets)
    
 

@router.get("/assets/create",response_model=DgtResponse)                                                                      
async def get_create_asset(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    dec, response = await get_dec_emission_key(query)
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={DEC_TOTAL_SUM : dec[DEC_TOTAL_SUM][DATTR_VAL] if DEC_TOTAL_SUM in dec else 0},                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            

@router.get("/assets/{asset_id}/pay",response_model=DgtResponse)                                                                      
async def get_pay_asset(request: Request,asset_id: str,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    dec, response = await get_dec_emission_key(query)
    supply = {}
    for attr in [DEC_TOTAL_SUM,DEC_MINTING_TOTAL,DEC_MINTING_REST,DEC_СORPORATE_TOTAL,DEC_СORPORATE_REST,DEC_SALE_TOTAL,DEC_SALE_REST]:
        supply[attr] = dec[attr] if not isinstance(dec[attr],dict) else dec[attr][DATTR_VAL]                                                                 
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=supply,                                                                                                       
        metadata=query._get_metadata(request, response))


@router.get("/assets/{asset_id}/invoice",response_model=DgtResponse)                                                                      
async def get_invoice(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    dec, response = await get_dec_emission_key(query)                                                                     
    keys = dec[DEC_EMISSION_INFO][DATTR_VAL]
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=keys,                                                                                                       
        metadata=query._get_metadata(request, response))

