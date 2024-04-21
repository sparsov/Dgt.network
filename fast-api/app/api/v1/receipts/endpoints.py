from fastapi import APIRouter
from fastapi import Depends, Request
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_receipt_pb2
from fastapi_pagination import Page, paginate
from app.schemas import DgtPagingListResponse, DgtResponse,DgtListResponse
from app.messaging.error_handlers import ReceiptNotFoundTrap
import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
router = APIRouter()


@router.get("/receipts") #,response_model=DgtPagingListResponse)
async def get_receipts(request: Request,id: str ='',query: QueryValidatorHandler = Depends(getQueryValidator)):
    """Fetches the receipts for transaction by either a POST or GET.                          
                                                                                               
     Request:                                                                                  
         body: A JSON array of one or more transaction id strings (if POST)                    
         query:                                                                                
             - id: A comma separated list of up to 15 ids (if GET)                             
             - wait: Request should return as soon as some receipts are                        
                 available                                                                     
                                                                                               
     Response:                                                                                 
         data: A JSON object, with transaction ids as keys, and receipts as                    
             values                                                                            
         link: The /receipts link queried (if GET)                                   
    """                                                                             
                                                                                               
    LOGGER.debug('get_receipts for validator')  
    error_traps = [ReceiptNotFoundTrap]
    ids = query._get_filter_ids(request)                                    
    if not ids:                                                            
        LOGGER.debug('Request for receipts missing id query')              
        raise errors.ReceiptIdQueryInvalid()                               
                                                                           
    # Query validator                                                   
    validator_query = client_receipt_pb2.ClientReceiptGetRequest(transaction_ids=ids)                                        
    query._set_wait(request, validator_query)                            
                                                                        
    response = await query._query_validator(                             
        Message.CLIENT_RECEIPT_GET_REQUEST,                             
        client_receipt_pb2.ClientReceiptGetResponse,                    
        validator_query,                                                
        error_traps)                                                    
    metadata = query._get_metadata(request, response)                                                                    
                                            
                                                                        
    data = query._drop_id_prefixes(query._drop_empty_props(response['receipts']))                   
                                                                        
    return query._wrap_response(request, data=data, metadata=metadata)   
    
    
    
    
                                                                                      
@router.post("/receipts",response_model=DgtResponse)
async def post_receipts(request: Request,transaction_id: str ='',query: QueryValidatorHandler = Depends(getQueryValidator)):                                                                                      
    """Fetches a specific transaction from the validator, specified by id.                                            
                                                                                                                      
    Request:                                                                                                          
        path:                                                                                                         
            - transaction_id: The 128-character id of the txn to be fetched                                           
                                                                                                                      
    Response:                                                                                                         
        data: A JSON object with the data from the expanded Transaction                                               
        link: The link to this exact query                                                                            
    """                                                                                                               
    LOGGER.debug('get_receipts for validator')  
    error_traps = [post_receipts] 
    if request.headers.get('Content-Type') != 'application/json':                    
        LOGGER.debug('Request headers had wrong Content-Type: %s',request.headers.get('Content-Type'))                                     
        raise errors.ReceiptWrongContentType()                                   
                                                                                 
    ids = await request.json()                                                   
                                                                                 
    if (not ids                                                                  
            or not isinstance(ids, list)                                         
            or not all(isinstance(i, str) for i in ids)):                        
        LOGGER.debug('Request body was invalid: %s', ids)                        
        raise errors.ReceiptBodyInvalid()                                        
    for i in ids:                                                                
        query._validate_id(i)  
        
    validator_query = client_receipt_pb2.ClientReceiptGetRequest(transaction_ids=ids)                                                
    query._set_wait(request, validator_query)                                    
                                                                                
    response = await query._query_validator(                                     
        Message.CLIENT_RECEIPT_GET_REQUEST,                                     
        client_receipt_pb2.ClientReceiptGetResponse,                            
        validator_query,                                                        
        error_traps)                                                            
                                                                                
    # Send response                                                                                                                
    data = query._drop_id_prefixes(query._drop_empty_props(response['receipts']))                       
                                                                            
    return query._wrap_response(request, data=data, metadata=None)       
    
    
