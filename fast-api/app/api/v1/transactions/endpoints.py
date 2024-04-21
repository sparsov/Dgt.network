from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_transaction_pb2
from fastapi_pagination import Page, paginate
from app.schemas import DgtPagingListResponse, DgtResponse
from app.messaging.error_handlers import TransactionNotFoundTrap
from app.utils.logger import logger as LOGGER
router = APIRouter()


@router.get("/transactions",response_model=DgtPagingListResponse)
async def get_transactions(request: Request,query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches list of txns from validator, optionally filtered by id.                                   
                                                                                                         
    Request:                                                                                             
        query:                                                                                           
            - head: The id of the block to use as the head of the chain                                  
            - id: Comma separated list of txn ids to include in results                                  
                                                                                                         
    Response:                                                                                            
        data: JSON array of Transaction objects with expanded headers                                    
        head: The head used for this query (most recent if unspecified)                                  
        link: The link to this exact query, including head block                                         
        paging: Paging info and nav, like total resources and a next link                                
    """                                                                                                  
    LOGGER.debug('list_transactions for validator')                                                      
                                                                                                         
    paging_controls = query._get_paging_controls(request)                                                 
    validator_query = client_transaction_pb2.ClientTransactionListRequest(                               
        head_id=query._get_head_id(request),                                                              
        transaction_ids=query._get_filter_ids(request),                                                   
        sorting=query._get_sorting_message(request, "default"),                                           
        paging=query._make_paging_message(paging_controls))                                               
                                                                                                         
    response = await query._query_validator(                                                              
        Message.CLIENT_TRANSACTION_LIST_REQUEST,                                                         
        client_transaction_pb2.ClientTransactionListResponse,                                            
        validator_query)                                                                                 
                                                                                                         
    data = [query._expand_transaction(t) for t in response['transactions']]                               
                                                                                                         
    return query._wrap_paginated_response(                                                                
        request=request,                                                                                 
        response=response,                                                                               
        controls=paging_controls,                                                                        
        data=data) 
                                                                                      
@router.get("/transactions/{transaction_id}",response_model=DgtResponse)
async def get_transaction(request: Request,transaction_id: str ='',query: QueryValidatorHandler = Depends(getQueryValidator)):                                                                                      
    """Fetches a specific transaction from the validator, specified by id.                                            
                                                                                                                      
    Request:                                                                                                          
        path:                                                                                                         
            - transaction_id: The 128-character id of the txn to be fetched                                           
                                                                                                                      
    Response:                                                                                                         
        data: A JSON object with the data from the expanded Transaction                                               
        link: The link to this exact query                                                                            
    """                                                                                                               
    error_traps = [TransactionNotFoundTrap]                                                            
                                                                                                                      
    #txn_id = request.match_info.get('transaction_id', '')                                                             
    query._validate_id(transaction_id)                                                                                         
                                                                                                                      
    response = await query._query_validator(                                                                           
        Message.CLIENT_TRANSACTION_GET_REQUEST,                                                                       
        client_transaction_pb2.ClientTransactionGetResponse,                                                          
        client_transaction_pb2.ClientTransactionGetRequest(transaction_id=transaction_id),                                                                                   
        error_traps)                                                                                                  
                                                                                                                      
    return query._wrap_response(                                                                                       
        request,                                                                                                      
        data=query._expand_transaction(response['transaction']),                                                       
        metadata=query._get_metadata(request, response))                                                               
    
    
    
    
    
    
    
