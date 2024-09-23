from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse,DgtResponse,PayTrans
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token
from app.utils.dec_utils import make_pay_send_trans,do_dec_op
router = APIRouter()



@router.post("/payments/send",response_model=DgtResponse)
async def post_pay_send(request: Request,pay : PayTrans,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # send coins
    sign_req,topts = make_pay_send_trans(vars(pay.info),pay.did,vars(pay.signed) if pay.signed else None)           
    response = await do_dec_op(request,topts,sign_req,query)                                                                       
                                                                                                                                   
    return query._wrap_response(                                                                                                     
        request,                                                                                                                    
        data=response,                                                                                                             
        metadata=query._get_metadata(request, response))                                                                             






@router.post("/payments/invoice",response_model=DgtResponse)                                                                      
async def post_pay_invoice(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    dec, response = await get_dec_emission_key(query)
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data={DEC_TOTAL_SUM : dec[DEC_TOTAL_SUM][DATTR_VAL] if DEC_TOTAL_SUM in dec else 0},                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            
                                                                            

@router.post("/payments/send-by-alias",response_model=DgtResponse)                                                                      
async def post_pay_by_alias(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    dec, response = await get_dec_emission_key(query)                                                                     
    keys = dec[DEC_EMISSION_INFO][DATTR_VAL]
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=keys,                                                                                                       
        metadata=query._get_metadata(request, response))

