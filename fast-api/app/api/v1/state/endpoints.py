from fastapi import APIRouter
from fastapi import Depends, Request
#from app.core.models import User, UserCreate
#from app.core.security import get_password_hash
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2
import app.messaging.error_handlers as error_handlers
from app.schemas import DgtPagingListResponse, DgtResponse
from app.utils.logger import logger as LOGGER
#from app.api.routers import router
router = APIRouter()


@router.get("/state",response_model=DgtPagingListResponse)
async def get_states(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches list of data entries, optionally filtered by address prefix.           
                                                                                      
    Request:                                                                          
        query:                                                                        
            - head: The id of the block to use as the head of the chain               
            - address: Return entries whose addresses begin with this                 
            prefix                                                                    
                                                                                      
    Response:                                                                         
        data: An array of leaf objects with address and data keys                     
        head: The head used for this query (most recent if unspecified)               
        link: The link to this exact query, including head block                      
        paging: Paging info and nav, like total resources and a next link             
    """                                                                               
    paging_controls = query._get_paging_controls(request)                              
    # for DAG ask head of chain for getting merkle root is incorrect way              
    # FIXME - add special method for asking real merkle root                          
    head, root = await query._head_to_root(request.query_params.get('head', None))        
    LOGGER.debug('LIST_STATE STATE=%s',root[:10])                                     
                                                                                      
    validator_query = client_state_pb2.ClientStateListRequest(                        
        state_root='',#root,                                                          
        address=request.query_params.get('address', None),                               
        sorting=query._get_sorting_message(request, "default"),                        
        paging=query._make_paging_message(paging_controls))                            
                                                                                      
    response = await query._query_validator(                                           
        Message.CLIENT_STATE_LIST_REQUEST,                                            
        client_state_pb2.ClientStateListResponse,                                     
        validator_query) 

    return query._wrap_paginated_response(
            request=request,
            response=response,
            controls=paging_controls,
            data=response.get('entries', []),
            head=head)                                                             
    
    
@router.get("/state/{address}",response_model=DgtResponse)
async def get_state(request: Request,address: str = '',query: QueryValidatorHandler = Depends(getQueryValidator)):

    """Fetches data from a specific address in the validator's state tree.                              
                                                                                                        
    Request:                                                                                            
        query:                                                                                          
            - head: The id of the block to use as the head of the chain                                 
            - address: The 70 character address of the data to be fetched                               
                                                                                                        
    Response:                                                                                           
        data: The base64 encoded binary data stored at that address                                     
        head: The head used for this query (most recent if unspecified)                                 
        link: The link to this exact query, including head block                                        
    """                                                                                                 
    error_traps = [                                                                                     
        error_handlers.InvalidAddressTrap,                                                              
        error_handlers.StateNotFoundTrap]                                                               
                                                                                                        
    #address = request.match_info.get('address', '')                                                     
    head = request.query_params.get('head', None)                                                          
    LOGGER.debug('fetch_state head=%s',head[:8] if head is not None else None)                          
    #FIXME for DAG we should ask real merkle root                                                       
    head, root = await query._head_to_root(head)                                                         
    response = await query._query_validator(                                                             
        Message.CLIENT_STATE_GET_REQUEST,                                                               
        client_state_pb2.ClientStateGetResponse,                                                        
        client_state_pb2.ClientStateGetRequest(                                                         
            state_root='',#root,                                                                        
            address=address),                                                                           
        error_traps)                                                                                    
                                                                                                        
    return query._wrap_response(                                                                         
        request,                                                                                        
        data=response['value'],                                                                         
        metadata=query._get_metadata(request, response, head=head))                                      
                                                                                                        
