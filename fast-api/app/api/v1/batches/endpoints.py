from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_batch_pb2, client_batch_submit_pb2
from fastapi_pagination import Page, paginate
from app.schemas import DgtPagingListResponse, DgtResponse, DgtListResponse
import app.messaging.error_handlers as error_handlers
import app.messaging.exceptions as errors
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
    error_traps = [error_handlers.BatchNotFoundTrap]                                    
                                                                                        
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
    
    
@router.get("/batch_statuses",response_model=DgtListResponse)
async def get_batch_statuses(request: Request,id:str,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches the committed status of batches by either a POST or GET.

    Request:
        body: A JSON array of one or more id strings (if POST)
        query:
            - id: A comma separated list of up to 15 ids (if GET)
            - wait: Request should not return until all batches committed

    Response:
        data: A JSON object, with batch ids as keys, and statuses as values
        link: The /batch_statuses link queried (if GET)
    """
    error_traps = [error_handlers.StatusResponseMissing]
    ids = query._get_filter_ids(request)
    if not ids:
        LOGGER.info('Request for statuses missing id query')
        raise errors.StatusIdQueryInvalid()


    # Query validator
    validator_query = client_batch_submit_pb2.ClientBatchStatusRequest(batch_ids=ids)
    query._set_wait(request, validator_query)
    LOGGER.info('Request for statuses id={}'.format(ids))
    response = await query._query_validator(
        Message.CLIENT_BATCH_STATUS_REQUEST,
        client_batch_submit_pb2.ClientBatchStatusResponse,
        validator_query,
        error_traps)

    # Send response
    metadata = query._get_metadata(request, response)

    data = query._drop_id_prefixes(query._drop_empty_props(response['batch_statuses']))

    return query._wrap_response(request, data=data, metadata=metadata)



@router.post("/batch_statuses") #,response_model=DgtResponse)
async def post_batch_statuses(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches the committed status of batches by either a POST or GET.
    Request:
        body: A JSON array of one or more id strings
        query:
            - wait: Request should not return until all batches committed

    Response:
        data: A JSON object, with batch ids as keys, and statuses as values
        link: The /batch_statuses link queried (if GET)
    """
    error_traps = [error_handlers.StatusResponseMissing]
    if request.headers['Content-Type'] != 'application/json':                                             
        LOGGER.debug(                                                                                     
            'Request headers had wrong Content-Type: %s',                                                 
            request.headers['Content-Type'])                                                              
        raise errors.StatusWrongContentType()                                                             
                                                                                                          
    ids = await request.json()                                                                            
                                                                                                          
    if (not ids                                                                                           
            or not isinstance(ids, list)                                                                  
            or not all(isinstance(i, str) for i in ids)):                                                 
        LOGGER.debug('Request body was invalid: %s', ids)                                                 
        raise errors.StatusBodyInvalid()                                                                  
    for i in ids:                                                                                         
        query._validate_id(i)                                                                              
    
    # Query validator                                                                                                                                                                                       
    validator_query =  client_batch_submit_pb2.ClientBatchStatusRequest(batch_ids=ids)                                                                            
    query._set_wait(request, validator_query)                                                          
                                                                                                      
    response = await query._query_validator(                                                           
        Message.CLIENT_BATCH_STATUS_REQUEST,                                                          
        client_batch_submit_pb2.ClientBatchStatusResponse,                                            
        validator_query,                                                                              
        error_traps)                                                                                  
                                                                                                      
    # Send response                                                                                   
                                                                                                      
    data = query._drop_id_prefixes(query._drop_empty_props(response['batch_statuses']))                                           
                                                                                                      
    return query._wrap_response(request, data=data, metadata=None)                                 
