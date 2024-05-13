from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.utils.dec_utils import get_dec_emission_key
from app.schemas import DgtListResponse,DgtResponse
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token
router = APIRouter()


   


@router.get("/emission/info",response_model=DgtResponse)
async def get_emission_info(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # dec show _DEC_EMISSION_KEY_
    dec, response = await get_dec_emission_key(query)
                                                                            
    return query._wrap_response(                                                
        request,                                                               
        data=dec,
        metadata=query._get_metadata(request, response))                        

@router.get("/emission/totalsupply",response_model=DgtResponse)                                                                      
async def get_totalsupply(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    dec, response = await get_dec_emission_key(query)
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={DEC_TOTAL_SUM : dec[DEC_TOTAL_SUM][DATTR_VAL] if DEC_TOTAL_SUM in dec else 0},                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            

@router.get("/emission/actualsupply",response_model=DgtResponse)                                                                      
async def get_actualsupply(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec distribute
    dec, response = await get_dec_emission_key(query)
    supply = {}
    for attr in [DEC_TOTAL_SUM,DEC_MINTING_TOTAL,DEC_MINTING_REST,DEC_СORPORATE_TOTAL,DEC_СORPORATE_REST,DEC_SALE_TOTAL,DEC_SALE_REST]:
        supply[attr] = dec[attr] if not isinstance(dec[attr],dict) else dec[attr][DATTR_VAL]                                                                 
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=supply,                                                                                                       
        metadata=query._get_metadata(request, response))


@router.get("/emission/emission_keys/list",response_model=DgtResponse)                                                                      
async def get_emission_keys(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    dec, response = await get_dec_emission_key(query)                                                                     
    keys = dec[DEC_EMISSION_INFO][DATTR_VAL]
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=keys,                                                                                                       
        metadata=query._get_metadata(request, response))

@router.get("/emission/minting",response_model=DgtResponse)
async def get_minting(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    dec, response = await get_dec_emission_key(query)
    mint = {DEC_MINT_PARAM    : dec[DEC_MINT_PARAM][DATTR_VAL],
            DEC_MINTING_SHARE : dec[DEC_MINTING_SHARE][DATTR_VAL],
            DEC_MINTING_TOTAL : dec[DEC_MINTING_TOTAL],
            DEC_MINTING_REST  : dec[DEC_MINTING_REST]

            }                                                                       
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=mint,                                                                                                       
        metadata=query._get_metadata(request, response))

@router.get("/emission/token_hold",response_model=DgtResponse)
async def get_token_hold(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    
    dec, response = await get_dec_emission_key(query)                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={},                                                                                                       
        metadata=query._get_metadata(request, response))                                                                          
                                                                                                                                      
