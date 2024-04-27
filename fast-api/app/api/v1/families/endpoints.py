from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
import app.messaging.error_handlers as error_handlers
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
from app.schemas import DgtResponse
from app.utils.logger import logger as LOGGER
from app.utils.signing import signer
from .bgt_utils import bgt_show, bgt_list,bgt_op
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

@router.get("/run") #,response_model=DgtResponse)
async def run_transaction(request: Request,family: str,cmd: str,query: QueryValidatorHandler = Depends(getQueryValidator)):
#async def run_transaction(self, request):                                                                                                      
    """                                                                                                                                        
    make transfer from wallet to wallet                                                                                                        
    """                                                                                                                                        
    if family == 'bgt' :                                                                                                                       
        if cmd == 'show':   
            resp = await bgt_show(request,query)                                                                                                                   
                                                                                      
        elif  cmd == 'list' :
            resp = await bgt_list(request,query)                                                                                                                   
            
        else:
            resp = await bgt_op(request,cmd,query)                                                                  
        return resp                                                                                                     
    else:                                                                                                                                      
        # undefined families                                                                                                                   
        return query._wrap_response(                                                                                                                
         request,                                                                                                                               
          data=None,                                                                                                                             
          metadata={                                                                                                                             
          'link': '',                                                                                                                        
         }                                                                                                                                      
        )                                                                                                                        



