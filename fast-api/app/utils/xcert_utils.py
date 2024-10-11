#from fastapi import APIRouter
from fastapi import Request
import app.messaging.error_handlers as error_handlers
from app.messaging import getQueryValidator, QueryValidatorHandler
from dgt_sdk.protobuf.validator_pb2 import Message
from dgt_sdk.protobuf import client_state_pb2,client_topology_pb2
from dgt_sdk.protobuf import client_batch_submit_pb2
#import app.messaging.error_handlers as error_handlers
#import app.messaging.exceptions as errors
from app.utils.logger import logger as LOGGER
from app.utils.signing import signer,_context
from app.utils.tnx_utils import create_batch, decode_signed
from x509_cert.client_cli.xcert_cmd_utils  import xcert_req_sign,do_did_req
import base64
import cbor

     
    

def make_did_trans(info,signed=None):
    if signed is None:
        LOGGER.debug('make_did_trans info={}'.format(info))
        signed = xcert_req_sign(vars(info.cert),signer,owner=info.owner)
        owner = info.owner
        LOGGER.debug('make_asset_trans info={} signed={}'.format(info,signed))
    else:
        #LOGGER.debug('make_asset_trans signed={}'.format(signed))
        signed,owner = decode_signed(signed)

    
    trans,did = do_did_req(info,signed,signer,owner)
    
    LOGGER.debug('make_did_trans did={} trans={}'.format(did,trans))
    # do trans params
    return trans,did


async def do_xcert_op(request: Request,trans,query: QueryValidatorHandler):

    batch = create_batch([trans],signer)                                      
    batch_id = batch.header_signature                                                                                                      

    if batch_id is not None:                                                                                                                   
        error_traps = [error_handlers.BatchInvalidTrap,error_handlers.BatchQueueFullTrap]                                                      
        validator_query = client_batch_submit_pb2.ClientBatchSubmitRequest(batches=[batch])                                                    
        LOGGER.debug('run_transaction send batch_id=%s',batch_id)                                                                              

        with query._post_batches_validator_time.time(): 
            query._post_batches_count.inc()                                                                                        
            response = await query._query_validator(                                                                                                       
                Message.CLIENT_BATCH_SUBMIT_REQUEST,                                                                                           
                client_batch_submit_pb2.ClientBatchSubmitResponse,                                                                             
                validator_query,                                                                                                               
                error_traps)  
                                                                                                                          
        link = query._build_url(request, path='/batch_statuses', id=batch_id) 
        #LOGGER.debug('run_transaction link={}'.format(link))
        response["link"] = link
        return response
                                                                                                                                     

