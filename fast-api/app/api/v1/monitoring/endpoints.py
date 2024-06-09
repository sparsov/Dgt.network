from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2

from app.schemas import DgtResponse
router = APIRouter()


@router.get("/network/metrics/tps",response_model=DgtResponse)
async def get_metrics_tps(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
              
                                                              
    return query._wrap_response(                               
        request,                                              
        data={},                               
        metadata=query._get_metadata(request, None))       
 
@router.get("/network/metrics/latency",response_model=DgtResponse)                                                   
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):             
                                                                                                              
                                                                                                              
    return query._wrap_response(                                                                              
        request,                                                                                              
        data={},                                                                                              
        metadata=query._get_metadata(request, None))   
                                                   



  
@router.get("/network/metrics/entropy",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       
                                                                                                                                                 
                                                                                                                                                 
    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))  
                                                                                       
@router.get("/network/metrics/node_activity",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None)) 

@router.get("/network/metrics/active_users",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))  
                                                                                       
@router.get("/network/metrics/blockchain_size",response_model=DgtResponse)                                                                                                                                
async def get_metrics_latency(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):                                       


    return query._wrap_response(                                                                                                                 
        request,                                                                                                                                 
        data={},                                                                                                                                 
        metadata=query._get_metadata(request, None))                                                                                         

                                                                                       

                                                                                        
                                                                                       
