from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2

from app.schemas import DgtResponse
router = APIRouter()


@router.get("/crypto/generate_address",response_model=DgtResponse)
async def get_generate_address(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
                
                                                              
    return query._wrap_response(                               
        request,                                              
        data={},                               
        metadata=query._get_metadata(request, None))   
    

@router.get("/crypto/get_public_key",response_model=DgtResponse)                                                
async def get_crypto_public_key(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):             
                                                                 
                                                                                                              
    return query._wrap_response(                                                                              
        request,                                                                                              
        data={},                                                                               
        metadata=query._get_metadata(request, None))                                                      
