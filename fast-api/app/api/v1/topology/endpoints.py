import base64
import json
from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_topology_pb2
from app.schemas import DgtResponse
#from app.api.routers import router
router = APIRouter()


@router.get("/topology",response_model=DgtResponse)
async def get_topology(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    response = await query._query_validator(                         
        Message.CLIENT_TOPOLOGY_GET_REQUEST,                        
        client_topology_pb2.ClientTopologyGetResponse,              
        client_topology_pb2.ClientTopologyGetRequest())             
    topology = base64.b64decode(response['topology'])               
    #LOGGER.debug('Request fetch_topology=%s',topology)             
    return query._wrap_response(                                     
        request,                                                    
        data=json.loads(topology),                                  
        metadata=query._get_metadata(request, response))             
