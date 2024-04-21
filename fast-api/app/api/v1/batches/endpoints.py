from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_batch_pb2
from fastapi_pagination import Page, paginate
from app.schemas import DgtPagingListResponse, DgtResponse
from app.messaging.error_handlers import BatchNotFoundTrap
from app.utils.logger import logger as LOGGER
router = APIRouter()


@router.get("/batches",response_model=DgtPagingListResponse)
async def get_batches(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches list of batches from validator, optionally filtered by id.                     
                                                                                              
    Request:                                                                                  
        query:                                                                                
            - head: The id of the block to use as the head of the chain                       
            - id: Comma separated list of batch ids to include in results                     
                                                                                              
    Response:                                                                                 
        data: JSON array of fully expanded Batch objects                                      
        head: The head used for this query (most recent if unspecified)                       
        link: The link to this exact query, including head block                              
        paging: Paging info and nav, like total resources and a next link                     
    """                                                                                       
    paging_controls = query._get_paging_controls(request)  
    LOGGER.debug("paging_controls={}".format(paging_controls))                                    
    validator_query = client_batch_pb2.ClientBatchListRequest(                                
        head_id=query._get_head_id(request),                                                   
        batch_ids=query._get_filter_ids(request),                                              
        sorting=query._get_sorting_message(request, "default"),                                
        paging=query._make_paging_message(paging_controls))                                    
                                                                                              
    response = await query._query_validator(                                                   
        Message.CLIENT_BATCH_LIST_REQUEST,                                                    
        client_batch_pb2.ClientBatchListResponse,                                             
        validator_query)  
    #LOGGER.debug("response={}".format(response))                                                                    
    #return paginate([])                                                                                         
    return query._wrap_paginated_response(                                                     
        request=request,                                                                      
        response=response,                                                                    
        controls=paging_controls,                                                             
        data=[query._expand_batch(b) for b in response['batches']])  
                          
@router.get("/batches/{batch_id}",response_model=DgtResponse)
async def get_batch(request: Request,batch_id: str ='',query: QueryValidatorHandler = Depends(getQueryValidator)):                          
    """Fetches a specific batch from the validator, specified by id.                    
                                                                                        
    Request:                                                                            
        path:                                                                           
            - batch_id: The 128-character id of the batch to be fetched                 
                                                                                        
    Response:                                                                           
        data: A JSON object with the data from the fully expanded Batch                 
        link: The link to this exact query                                              
    """                                                                                 
    error_traps = [BatchNotFoundTrap]                                    
                                                                                        
    #batch_id = request.match_info.get('batch_id', '')                                   
    LOGGER.debug(f'fetch_batch batch_id={batch_id}')                                    
    query._validate_id(batch_id)                                                         
    LOGGER.debug(f'fetch_batch _query_validator ..')                                    
    response = await query._query_validator(                                             
        Message.CLIENT_BATCH_GET_REQUEST,                                               
        client_batch_pb2.ClientBatchGetResponse,                                        
        client_batch_pb2.ClientBatchGetRequest(batch_id=batch_id),                      
        error_traps)                                                                    
                                                                                                                 
    return query._wrap_response(                                                                                   
        request,                                                                                                 
        data=query._expand_batch(response['batch']),                                     
        metadata=query._get_metadata(request, response))                                 
    
    
    
    
    
    
    
    
    
