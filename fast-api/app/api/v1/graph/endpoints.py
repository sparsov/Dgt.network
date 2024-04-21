from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2
from app.schemas import DgtListResponse

router = APIRouter()


@router.get("/graph",response_model=DgtListResponse)
async def get_status(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    response = await query._query_validator(                   
        Message.CLIENT_PEERS_GET_REQUEST,                     
        client_peers_pb2.ClientPeersGetResponse,              
        client_peers_pb2.ClientPeersGetRequest())             
                                                              
    return query._wrap_response(                               
        request,                                              
        data=response['peers'],                               
        metadata=query._get_metadata(request, response))       
    
