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
import base64
import cbor

     
    

def make_did_trans(info,signed=None):
    if signed is None:
        LOGGER.debug('make_did_trans info={}'.format(info))
        signed = do_signed_did_req(info,signer,did)
        LOGGER.debug('make_asset_trans info={} signed={}'.format(info,signed))
    else:
        #LOGGER.debug('make_asset_trans signed={}'.format(signed))
        signed,_ = decode_signed(signed)


    sign_req,hdr,topts,addr = do_target_req(info,signed,tips,signer,did)
    
    LOGGER.debug('make_did_trans req={} topts={} tips={}'.format(sign_req,topts,tips))
    # do trans params
    return sign_req,topts,addr


async def do_xcert_op(request: Request,topts: dict,info: dict,query: QueryValidatorHandler):
    to      = topts[DEC_CMD_TO] if DEC_CMD_TO in topts else None                                                        
    din     = topts[DEC_CMD_DIN] if DEC_CMD_DIN in topts else None                                                      
    din_ext = topts[DEC_CMD_DIN_EXT] if DEC_CMD_DIN_EXT in topts else None                                              
    #return self._send_transaction(topts[DEC_CMD], topts[DEC_CMD_ARG], info, to=to, wait=wait,din=din,din_ext=din_ext)   
    # verb, name, value, to=None, wait=None,din=None,din_ext=None):    
    transaction = make_dec_transaction(signer,topts[DEC_CMD],topts[DEC_CMD_ARG],info,to,din,din_ext)          
    batch = create_batch([transaction],signer)                                      
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
                                                                                                                                     

