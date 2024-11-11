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
from app.utils.logger import logger as LOGGER
from dgt_validator.gossip.fbft_topology import FbftTopology
#from app.api.routers import router
router = APIRouter()

async def req_topology(query):
    response = await query._query_validator(                         
        Message.CLIENT_TOPOLOGY_GET_REQUEST,                        
        client_topology_pb2.ClientTopologyGetResponse,              
        client_topology_pb2.ClientTopologyGetRequest())             
    topology = base64.b64decode(response['topology']) 
    return json.loads(topology),response







@router.get("/topology",response_model=DgtResponse)
async def get_topology(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    topology,response = await req_topology(query)
                  
    #LOGGER.debug('Request fetch_topology=%s',topology)             
    return query._wrap_response(                                     
        request,                                                    
        data=topology,                                  
        metadata=query._get_metadata(request, response))             

@router.get("/ping",response_model=DgtResponse)
async def get_ping(request: Request,node: str, query: QueryValidatorHandler = Depends(getQueryValidator)):

    topology,response = await req_topology(query)
    fbft = FbftTopology()                                                                             
    fbft.get_topology(topology,'','','static')
    LOGGER.debug('Request ping={} gates={}'.format(node,fbft.gates))             
    return query._wrap_response(                                     
        request,                                                    
        data=topology,                                  
        metadata=query._get_metadata(request, response))             

