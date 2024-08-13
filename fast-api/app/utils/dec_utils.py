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
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import _get_full_addr as get_full_addr, loads_dec_token, _get_full_prefix, loads_dec_entries
from dec_dgt.client_cli.dec_cmd_utils import (do_signed_target_req,do_target_req,get_this_tips,
                                              make_dec_transaction,
                                              do_signed_wallet_req,do_wallet_req,
                                              do_signed_invoice_req,do_invoice_req
                                              )
from app.utils.signing import signer,_context
from app.utils.tnx_utils import create_batch
import base64
import cbor

async def get_dec_emission_key(query: QueryValidatorHandler):
    address = get_full_addr(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)
    LOGGER.debug('Request get_dec_emission_key addr={}'.format(address))                     
    response = await query.get_state_by_addr(address=address)                                                                                            
    #LOGGER.debug('response={}'.format(response))                 
    dec = loads_dec_token(response['value'],DEC_EMISSION_KEY)
    return dec, response  
   

async def get_dec_entries(request: Request,address: str,query: QueryValidatorHandler):
    
    LOGGER.debug('Request get_dec_entries addr={}'.format(address))                     
    response = await query.get_states_by_addr(request,address)                                                                                            
    #LOGGER.debug('response={}'.format(response))  
    entries = loads_dec_entries(response['entries'])
    return entries, response  


async def get_dec_accounts(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_WALLET_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)
   
    return entries, response  

async def get_dec_account_by_id(request: Request,account_id: str,query: QueryValidatorHandler):
    address = get_full_addr(account_id,DEC_WALLET_GRP,DEFAULT_DID)
    response = await query.get_state_by_addr(address=address)
    wallet = loads_dec_token(response['value'],account_id)
    
   
    return wallet, response  



async def get_dec_aliases(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_SYNONYMS_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)

    return entries, response  

async def get_dec_alias_by_id(request: Request,alias_id: str,query: QueryValidatorHandler):
    address = get_full_addr(alias_id,DEC_SYNONYMS_GRP,DEFAULT_DID)
    response = await query.get_state_by_addr(address=address)
    alias = loads_dec_token(response['value'],alias_id)


    return alias, response  


async def get_dec_assets(request: Request,query: QueryValidatorHandler):
    address = _get_full_prefix(DEC_TARGET_GRP,DEFAULT_DID)
    entries, response = await get_dec_entries(request,address,query)
   
    return entries, response 

async def get_gates_tips(request: Request,query: QueryValidatorHandler):  
    response = await query._query_validator(                         
        Message.CLIENT_GATE_GET_REQUEST,                           
        client_topology_pb2.ClientGateGetResponse,                   
        client_topology_pb2.ClientGateGetRequest()
        )                                             

                    
    bgates = base64.b64decode(response['gates']) 
    gates = json.loads(bgates)                     
    #LOGGER.debug('Request get_gates_tips=%s',gates)              
    return gates      
    
def decode_signed(signed):
    payload = base64.b64decode(signed["payload"])                  
    designed = {                                                     
            DEC_EMITTER           : signed["emitter"],             
            DEC_PAYLOAD_SIGNATURE : signed["signature"],           
            DEC_PAYLOAD           : payload                        
        }  
    ret = signer.verify(signed["signature"], payload,_context.pub_from_hex(signed["emitter"]) )    
    if not ret:                                                                                      
        print('BAD SIGN')                                                                            
    
                                                            
    LOGGER.debug('make_asset_trans CHECK={} payload={}'.format(ret,designed)) 
    return designed,signed["emitter"]   


def make_asset_trans(gates_tips,info,did,signed=None):
    if signed is None:
        info[DEC_TARGET_PRICE] = info[DEC_PRICE]
        del info[DEC_PRICE]

        signed = do_signed_target_req(info,signer,did)
        LOGGER.debug('make_asset_trans info={} signed={}'.format(info,signed))
    else:
        #LOGGER.debug('make_asset_trans signed={}'.format(signed))
        signed,_ = decode_signed(signed)

    # sign by this gate DEFAULT_GATE
    tips = get_this_tips(gates_tips)
    sign_req,hdr,topts,addr = do_target_req(info,signed,tips,signer,did)
    
    LOGGER.debug('make_asset_trans req={} topts={} tips={}'.format(sign_req,topts,tips))
    # do trans params
    return sign_req,topts,addr


async def do_dec_op(request: Request,topts: dict,info: dict,query: QueryValidatorHandler):
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
            response = await query._query_validator(                                                                                                       
                Message.CLIENT_BATCH_SUBMIT_REQUEST,                                                                                           
                client_batch_submit_pb2.ClientBatchSubmitResponse,                                                                             
                validator_query,                                                                                                               
                error_traps)  
                                                                                                                          
        link = query._build_url(request, path='/batch_statuses', id=batch_id) 
        #LOGGER.debug('run_transaction link={}'.format(link))
        response["link"] = link
        return response
                                                                                                                                     



def make_account_trans(info,did,signed=None):
    if signed is None:

        LOGGER.debug('make_accont_trans info={} did={}'.format(info,did))
        req,publey = do_signed_wallet_req(info,did,signer)
        LOGGER.debug('make_accont_trans req={} publey={}'.format(req,publey))
        
    else:
        req,publey = decode_signed(signed)
        
    
    freq,topts,addr = do_wallet_req(info,req,publey,signer,did)
    LOGGER.debug('make_accont_trans freq={} topts={}'.format(freq,topts))
    
    return freq,topts,addr

def make_invoice_trans(info,did,signed=None):
    LOGGER.debug('make_invoice_trans info={} did={}'.format(info,did))
    if signed:
        #
        req,pubkey = decode_signed(signed)
        inv = cbor.loads(req[DEC_PAYLOAD])[DEC_PAYLOAD][DEC_INVOICE_OP]
        print(inv)
    else: 
        req,pubkey = do_signed_invoice_req(info,did,signer)
        inv = info

    freq,topts,addr = do_invoice_req(inv,req,pubkey,signer,did)
    LOGGER.debug('make_invoice_trans freq={} topts={}'.format(freq,topts))
    return freq,topts,addr
