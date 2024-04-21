from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_status_pb2

#from app.api.routers import router
router = APIRouter()


@router.get("/status") # response_model=User)
async def get_status(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
                                                                                      
    response = await query._query_validator(                                           
        Message.CLIENT_STATUS_GET_REQUEST,                                            
        client_status_pb2.ClientStatusGetResponse,                                    
        client_status_pb2.ClientStatusGetRequest())                                   
                                                                                      
    return query._wrap_response(                                                       
        request,                                                                      
        data={                                                                        
            'peers': response['peers'],                                               
            'endpoint': response['endpoint']                                          
        },                                                                            
        metadata=query._get_metadata(request, response)
        )                               
