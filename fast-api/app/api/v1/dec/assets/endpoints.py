from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse, DgtResponse, DgtPagingDictResponse, AssetCreate,InvoiceCreate,PayTrans
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token
from app.utils.dec_utils import get_dec_assets,make_asset_trans,get_gates_tips,do_dec_op,make_invoice_trans,make_pay_asset_trans
from argparse import Namespace
import base64
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
    
 

@router.post("/assets/create",response_model=DgtResponse)                                                                      
async def post_create_asset(request: Request,asset: AssetCreate,query: QueryValidatorHandler = Depends(getQueryValidator)): 
    #       
    #args = Namespace(**vars(asset.info))                   
    #LOGGER.debug('request asset={} pay={}'.format(asset.info,asset.signed)) 
    gates_tips = await get_gates_tips(request,query)
    # bytes_field = b"Hello, world!"
    # encoded_bytes = base64.b64encode(bytes_field)

    #encoded_bytes = request.json()["bytes_field"]
    #bytes_field = base64.b64decode(encoded_bytes) 
    sign_req,topts,addr = make_asset_trans(gates_tips,vars(asset.info),asset.did,vars(asset.signed) if asset.signed else None) 
    response = await do_dec_op(request,topts,sign_req,query)
    response["addr"] = addr                                                                                                                                 
    return query._wrap_response(                           
        request,                                           
        data=response,                                     
        metadata=query._get_metadata(request, response)    
        )                                                   
    
                                                                            

@router.post("/assets/{asset_id}/pay",response_model=DgtResponse)                                                                      
async def post_pay_asset(request: Request,asset_id: str,pay : PayTrans,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # pay for asset 
    LOGGER.debug('post_pay_asset asset_id={} pay={}'.format(asset_id,pay))
    sign_req,topts = make_pay_asset_trans(asset_id,vars(pay.info),pay.did,vars(pay.signed) if pay.signed else None)
    response = await do_dec_op(request,topts,sign_req,query)
    
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response,                                                                                                       
        metadata=query._get_metadata(request, response))


@router.post("/assets/{asset_id}/invoice",response_model=DgtResponse)                                                                      
async def post_invoice(request: Request,invoice : InvoiceCreate,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # 
    sign_req,topts,addr = make_invoice_trans(vars(invoice.info),invoice.did,vars(invoice.signed) if invoice.signed else None)
    LOGGER.debug('request invoice={}'.format(topts))
    response = await do_dec_op(request,topts,sign_req,query)
    response["addr"] = addr
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response,                                                                                                       
        metadata=query._get_metadata(request, response))

