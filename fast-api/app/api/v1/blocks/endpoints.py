from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_block_pb2
from fastapi_pagination import Page, paginate
from app.schemas import DgtPagingListResponse, DgtResponse
from app.messaging.error_handlers import BlockNotFoundTrap
from app.utils.logger import logger as LOGGER
router = APIRouter()


@router.get("/blocks",response_model=DgtPagingListResponse)
async def get_blocks(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches list of blocks from validator, optionally filtered by id.                            
                                                                                                    
    Request:                                                                                        
        query:                                                                                      
            - head: The id of the block to use as the head of the chain                             
            - id: Comma separated list of block ids to include in results                           
                                                                                                    
    Response:                                                                                       
        data: JSON array of fully expanded Block objects                                            
        head: The head used for this query (most recent if unspecified)                             
        link: The link to this exact query, including head block                                    
        paging: Paging info and nav, like total resources and a next link                           
    """                                                                                             
    paging_controls = query._get_paging_controls(request)                                            
    validator_query = client_block_pb2.ClientBlockListRequest(                                      
        head_id=query._get_head_id(request),                                                         
        block_ids=query._get_filter_ids(request),                                                    
        sorting=query._get_sorting_message(request, "block_num"),                                    
        paging=query._make_paging_message(paging_controls))                                          
                                                                                                    
    response = await query._query_validator(                                                         
        Message.CLIENT_BLOCK_LIST_REQUEST,                                                          
        client_block_pb2.ClientBlockListResponse,                                                   
        validator_query)                                                                            
                                                                                                    
    return query._wrap_paginated_response(                                                           
        request=request,                                                                            
        response=response,                                                                          
        controls=paging_controls,                                                                   
        data=[query._expand_block(b) for b in response['blocks']])                                   
    
@router.get("/blocks/{block_id}",response_model=DgtResponse)   
async def get_block(request: Request,block_id: str='',query: QueryValidatorHandler = Depends(getQueryValidator)):    
   """Fetches a specific block from the validator, specified by id.                                 
   Request:                                                                                         
       path:                                                                                        
           - block_id: The 128-character id of the block to be fetched                              
                                                                                                    
   Response:                                                                                        
       data: A JSON object with the data from the fully expanded Block                              
       link: The link to this exact query                                                           
   """                                                                                              
   error_traps = [BlockNotFoundTrap]                                                 
                                                                                                    
   #block_id = request.match_info.get('block_id', '')                                                
   query._validate_id(block_id)                                                                      
                                                                                                    
   response = await query._query_validator(                                                          
       Message.CLIENT_BLOCK_GET_BY_ID_REQUEST,                                                      
       client_block_pb2.ClientBlockGetResponse,                                                     
       client_block_pb2.ClientBlockGetByIdRequest(block_id=block_id),                               
       error_traps)                                                                                 
                                                                                                    
   return query._wrap_response(                                                                                         
       request,                                                                                                         
       data=query._expand_block(response['block']),                                                                     
       metadata=query._get_metadata(request, response))                                                                 
                                                                                                    
   
   
   
   
   
   
   
   
   
