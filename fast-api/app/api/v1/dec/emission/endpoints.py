from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_heads_pb2
from app.utils.logger import logger as LOGGER
from app.schemas import DgtListResponse
router = APIRouter()


@router.get("/emission/info",response_model=DgtListResponse)
async def get_emission_info(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    # dec show _DEC_EMISSION_KEY_
    #head_id = request.match_info.get('head_id', '')                            
    LOGGER.debug('Request fetch_heads head_id=%s',head_id)                     
    response = await query._query_validator(                                    
        Message.CLIENT_HEADS_GET_REQUEST,                                      
        client_heads_pb2.ClientHeadsGetResponse,                               
        client_heads_pb2.ClientHeadsGetRequest(head_id=head_id))               
                                                                               
    return query._wrap_response(                                                
        request,                                                               
        data=response['heads'],                                                
        metadata=query._get_metadata(request, response))                        

@router.get("/emission/totalsupply",response_model=DgtListResponse)                                                                      
async def get_totalsupply(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    
    response = await query._query_validator(                                                                                          
        Message.CLIENT_HEADS_GET_REQUEST,                                                                                             
        client_heads_pb2.ClientHeadsGetResponse,                                                                                      
        client_heads_pb2.ClientHeadsGetRequest(head_id=''))                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response['heads'],                                                                                                       
        metadata=query._get_metadata(request, response))  
                                                                            

@router.get("/emission/actualsupply",response_model=DgtListResponse)                                                                      
async def get_actualsupply(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    
    response = await query._query_validator(                                                                                          
        Message.CLIENT_HEADS_GET_REQUEST,                                                                                             
        client_heads_pb2.ClientHeadsGetResponse,                                                                                      
        client_heads_pb2.ClientHeadsGetRequest(head_id=''))                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response['heads'],                                                                                                       
        metadata=query._get_metadata(request, response))


@router.get("/emission/emission_keys/list",response_model=DgtListResponse)                                                                      
async def get_emission_keys(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    # dec show _DEC_EMISSION_SIG_
    
    response = await query._query_validator(                                                                                          
        Message.CLIENT_HEADS_GET_REQUEST,                                                                                             
        client_heads_pb2.ClientHeadsGetResponse,                                                                                      
        client_heads_pb2.ClientHeadsGetRequest(head_id=''))                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response['heads'],                                                                                                       
        metadata=query._get_metadata(request, response))

@router.get("/emission/minting",response_model=DgtListResponse)
async def get_minting(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    
    response = await query._query_validator(                                                                                          
        Message.CLIENT_HEADS_GET_REQUEST,                                                                                             
        client_heads_pb2.ClientHeadsGetResponse,                                                                                      
        client_heads_pb2.ClientHeadsGetRequest(head_id=''))                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response['heads'],                                                                                                       
        metadata=query._get_metadata(request, response))

@router.get("/emission/token_hold",response_model=DgtListResponse)
async def get_token_hold(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                           
    
    
    response = await query._query_validator(                                                                                          
        Message.CLIENT_HEADS_GET_REQUEST,                                                                                             
        client_heads_pb2.ClientHeadsGetResponse,                                                                                      
        client_heads_pb2.ClientHeadsGetRequest(head_id=''))                                                                      
                                                                                                                                      
    return query._wrap_response(                                                                                                      
        request,                                                                                                                      
        data=response['heads'],                                                                                                       
        metadata=query._get_metadata(request, response))                                                                          
                                                                                                                                      
