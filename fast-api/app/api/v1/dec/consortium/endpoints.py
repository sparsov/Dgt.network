from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse,DgtResponse
from app.utils.dec_utils import get_dec_emission_key
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token
router = APIRouter()



@router.get("/consortium/address",response_model=DgtResponse)
async def get_consortium_addr(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # dec show _DEC_EMISSION_KEY_
    dec, response = await get_dec_emission_key(query)
                                                                            
    return query._wrap_response(                                                
        request,                                                               
        data={DEC_СORPORATE_ACCOUNT: dec[DEC_СORPORATE_ACCOUNT][DATTR_VAL]},
        metadata=query._get_metadata(request, response))                        

@router.get("/consortium/consortium_keys",response_model=DgtResponse)                                                                      
async def get_consortium_keys(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    dec, response = await get_dec_emission_key(query)
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={DEC_CORPORATE_PUB_KEY : dec[DEC_CORPORATE_PUB_KEY][DATTR_VAL] if DEC_CORPORATE_PUB_KEY in dec else {}},                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            
                                                                            

@router.get("/consortium/info",response_model=DgtResponse)                                                                      
async def get_consortium_info(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    dec, response = await get_dec_emission_key(query) 
    emiss = dec[DEC_EMISSION_INFO][DATTR_VAL]                                                                    
    info = { DEC_СORPORATE_SHARE: dec[DEC_СORPORATE_SHARE][DATTR_VAL],
             DEC_СORPORATE_TOTAL: dec[DEC_СORPORATE_TOTAL],
             DEC_СORPORATE_REST : dec[DEC_СORPORATE_REST],

            }
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=info,                                                                                                       
        metadata=query._get_metadata(request, response))


