from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_peers_pb2
from app.schemas import DgtResponse
from app.utils.logger import logger as LOGGER
router = APIRouter()

TX_FAMILIES = {
    'bgt': {'commands' :{'set':['wallet','amount'],'inc':['wallet','amount'],'dec':['wallet','amount'],'trans':['wallet','amount','to'],'show':['wallet']}}
}

@router.get("/tx_families",response_model=DgtResponse)
async def get_tx_families(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """                                                                                    
    get  tx families                                                                       
    """                                                                                    
    LOGGER.debug('Request tx_families endpoint=%s',request)                                
    return query._wrap_response(                                                            
        request,                                                                           
        data=TX_FAMILIES,
        metadata=query._get_metadata(request, None)                                                                   
        )  
