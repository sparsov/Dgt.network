
from fastapi import  Request
import app.messaging.error_handlers as error_handlers
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2, client_batch_submit_pb2

from app.utils.logger import logger as LOGGER
from app.messaging import QueryValidatorHandler
from app.utils.signing import signer
from app.utils.tnx_utils import create_batch
from dgt_bgt.client_cli.generate import BgtPayload,create_bgt_transaction,loads_bgt_token    
from dgt_bgt.processor.handler import make_bgt_address, make_bgt_prefix

async def bgt_show(request: Request,query: QueryValidatorHandler):
    wallet = request.query_params.get('wallet', None) 
    address = make_bgt_address(wallet)  
    response = await query.get_state_by_addr(address=address)                                                                            
                                                                                                  
    LOGGER.debug('run_transaction: BGT show=%s (%s)!',wallet,response)                                              
    if response['status'] == 'OK':                                                                                
        bgt = loads_bgt_token(response['value'],wallet)                                                             
        LOGGER.debug('run_transaction: BGT[%s]=%s!',wallet,bgt)                                                     
    else:                                                                                                         
        bgt = response['value']                                                                                   

    return query._wrap_response(                          
        request,                                          
        data=bgt,                                         
        metadata=query._get_metadata(request, response)
        )  





async def bgt_list(request: Request,query: QueryValidatorHandler):
    paging_controls = query._get_paging_controls(request)                                              
    # for DAG ask head of chain for getting merkle root is incorrect way                               
    # FIXME - add special method for asking real merkle root                                           
    head, root = await query._head_to_root(request.query_params.get('head', None))                     
    LOGGER.debug('LIST_STATE STATE=%s',root[:10])                                                      
                                                                                                       
    validator_query = client_state_pb2.ClientStateListRequest(                                         
        state_root='',                                                                                 
        address=make_bgt_prefix(),                                                                     
        sorting=query._get_sorting_message(request, "default"),                                        
        paging=query._make_paging_message(paging_controls))                                            
                                                                                                       
    response = await query._query_validator(                                                           
        Message.CLIENT_STATE_LIST_REQUEST,                                                             
        client_state_pb2.ClientStateListResponse,                                                      
        validator_query)                                                                               
                                                                                                       
    if response['status'] == 'OK':                                                                     
        decoded = []                                                                                   
        for entry in response['entries']:                                                              
            bgt = loads_bgt_token(entry["data"])                                                       
            LOGGER.debug(f'BGT LIST DATA={bgt}')                                                       
            decoded.append(bgt)                                                                        
        response['entries'] = decoded                                                                  
                                                                                                       
    return query._wrap_paginated_response(                                                             
        request=request,                                                                               
        response=response,                                                                             
        controls=paging_controls,                                                                      
        data=response.get('entries', []),                                                              
        head=head)                                                                                     
                                                                                                       

async def bgt_op(request: Request,cmd: str,query: QueryValidatorHandler):
    arg1 = request.query_params.get('wallet', None)
    arg2 = request.query_params.get('amount', None)                                                                                           
    arg3 = request.query_params.get('to', None)                                                                                               
    LOGGER.debug('run_transaction family=BGT cmd=%s(%s,%s)!!!',cmd,arg1,arg2)                             
    transaction = create_bgt_transaction(verb=cmd,name=arg1,value=int(arg2),signer=signer,to=arg3)                                   
    batch = create_batch([transaction],signer)                                                                                              
    batch_id = batch.header_signature                                                                                                      

    if batch_id is not None:                                                                                                                   
        error_traps = [error_handlers.BatchInvalidTrap,error_handlers.BatchQueueFullTrap]                                                      
        validator_query = client_batch_submit_pb2.ClientBatchSubmitRequest(batches=[batch])                                                    
        LOGGER.debug('run_transaction send batch_id=%s',batch_id)                                                                              

        with query._post_batches_validator_time.time():                                                                                         
            await query._query_validator(                                                                                                       
                Message.CLIENT_BATCH_SUBMIT_REQUEST,                                                                                           
                client_batch_submit_pb2.ClientBatchSubmitResponse,                                                                             
                validator_query,                                                                                                               
                error_traps)                                                                                                                   
        link = query._build_url(request, path='/batch_statuses', id=batch_id) 
                                                                          
    return query._wrap_response(                                                                                                                
        request,                                                                                                                               
        data=None,                                                                                                                             
        metadata={                                                                                                                             
          'link': link,                                                                                                                        
        }                                                                                                                                      
        )                                                                                                                                      



