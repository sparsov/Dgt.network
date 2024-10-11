# Copyright 2017 DGT NETWORK INC © Stanislav Parsov
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import hashlib
import base64
import time
import random
import requests
import yaml
import cbor
import json
import logging
from dgt_signing import create_context
from dgt_signing import CryptoFactory
from dgt_signing import ParseError
from dgt_signing.core import (X509_COMMON_NAME, X509_USER_ID,X509_BUSINESS_CATEGORY,X509_SERIAL_NUMBER)
from dgt_signing import key_to_dgt_addr,DGT_ADDR_PREF

from dgt_sdk.protobuf.transaction_pb2 import TransactionHeader
from dgt_sdk.protobuf.transaction_pb2 import Transaction
from dgt_sdk.protobuf.batch_pb2 import BatchList
from dgt_sdk.protobuf.batch_pb2 import BatchHeader
from dgt_sdk.protobuf.batch_pb2 import Batch
from cert_common.protobuf.x509_cert_pb2 import X509CertInfo

from x509_cert.client_cli.exceptions import XcertClientException,XcertClientKeyfileException
from x509_cert.client_cli.xcert_attr import *
LOGGER = logging.getLogger(__name__)

NOTARY_TYPES = [KEYKEEPER_ID,NOTARY_LEADER_ID,NOTARY_FOLOWER_ID,NOTARY_LIST_ID]


def _sha256(data):
    return hashlib.sha256(data).hexdigest()

def _sha512(data):                          
    return hashlib.sha512(data).hexdigest() 

def _get_prefix():                                             
    return _sha512(FAMILY_NAME.encode('utf-8'))[0:6]                     
                                                                   
def _get_address(name):                                      
    prefix = _get_prefix()                                    
    game_address = _sha512(name.encode('utf-8'))[64:]              
    return prefix + game_address  
                                 
def _token_info(val):
    token = X509CertInfo()
    token.ParseFromString(val)
    return token

def write_conf(conf,fconf=NOTARY_CONF_NM):                     
    with open(fconf,"w") as vfile:                             
        try:                                                   
            vfile.write(json.dumps(conf,indent=2))             
            LOGGER.info(f"SAVE VCONF = {conf}")                
        except Exception as ex:                                
            LOGGER.info(f"CANT SAVE VCONF={fconf} err={ex}")   

def read_conf(fconf=NOTARY_CONF_NM):                                 
    try:                                                             
        with open(fconf,"r") as vfile:                               
            info =  json.load(vfile)                                 
                                                                     
    except Exception as ex:                                          
        LOGGER.info(f"CANT READ VCONF = {ex}")                       
        info = {}                                                    
    LOGGER.info(f"VCONF = {info}")                                   
    return info    
  
  
  
  
def req2b64(req):                                                                                                                     
    req[XCERT_PAYLOAD] = base64.b64encode(req[XCERT_PAYLOAD]).decode('utf-8')                                                             
    return req                                                                                                                        
                                                
                                                
def xcert_req_sign(info,signer,owner = None):                                                                                                                                                       
    # sign dec request by owner                                                                                                                                                      
    # info - data relating to dec operation                                                                                                                                          
    #                                                                                                                                                                                
                                                                                                                                                                                     
    # this is header of request with owner sign                                                                                                                                      
    req_header = {                                                                                                                                                                   
            XCERT_EMITTER     : signer.get_public_key().as_hex() if owner is None else owner,                                                                                                                      
            XCERT_PAYLOAD     : info                                                                                                                                                   
                                                                                                                                                                                     
    }                                                                                                                                                                                
    payload = cbor.dumps(req_header)                                                                                                                                                 
    psignature = signer.sign(payload)                                                                                                                                                
    #                                                                                                                                                                                
    #  NotaryRequest is body of request with signed header                                                                                                                           
    #                                                                                                                                                                                
    req = {                                                                                                                                                                          
            XCERT_EMITTER           : req_header[XCERT_EMITTER],                                                                                                                         
            XCERT_PAYLOAD_SIGNATURE : psignature,                                                                                                                                      
            XCERT_PAYLOAD           : payload                                                                                                                                          
        }                                                                                                                                                                            
    #ret = self._signer.verify(psignature, payload,self._context.pub_from_hex(info[DEC_EMITTER]) )                                                                                   
    #if not ret:                                                                                                                                                                     
    #    print('BAD SIGN')                                                                                                                                                           
    return req                                                                                                                                                                       
                                                                    
def _make_xcert_transaction(signer, verb, name, value,to=None):                                                                                                                                
    val = {                                                                                                                                                                                  
        'Verb': verb,                                                                                                                                                                        
        'Owner': name,                                                                                                                                                                       
        'Value': value,                                                                                                                                                                      
    }                                                                                                                                                                                        
    if to is not None:                                                                                                                                                                       
        val['To'] = to                                                                                                                                                                       
    payload = cbor.dumps(val)                                                                                                                                                                
                                                                                                                                                                                             
    # Construct the address                                                                                                                                                                  
    address = _get_address(name)                                                                                                                                                        
    inputs = [address]                                                                                                                                                                       
    outputs = [address] 
    inputs.append(_get_address(NOTARY_LIST_ID))
    #print("NAME={} ADDR={}".format(name,address))                                                                                                                                                                     
    if to is not None:                                                                                                                                                                       
        address_to = _get_address(to)                                                                                                                                                   
        inputs.append(address_to)                                                                                                                                                            
        outputs.append(address_to)                                                                                                                                                           
                                                                                                                                                                                             
    header = TransactionHeader(                                                                                                                                                              
        signer_public_key=signer.get_public_key().as_hex(),                                                                                                                            
        family_name=FAMILY_NAME,                                                                                                                                                             
        family_version=FAMILY_VERSION,                                                                                                                                                       
        inputs=inputs,                                                                                                                                                                       
        outputs=outputs,                                                                                                                                                                     
        dependencies=[],                                                                                                                                                                     
        payload_sha512=_sha512(payload),                                                                                                                                                     
        batcher_public_key=signer.get_public_key().as_hex(),                                                                                                                           
        nonce=hex(random.randint(0, 2**64))                                                                                                                                                  
    ).SerializeToString()                                                                                                                                                                    
                                                                                                                                                                                             
    signature = signer.sign(header)                                                                                                                                                    
                                                                                                                                                                                             
    transaction = Transaction(                                                                                                                                                               
        header=header,                                                                                                                                                                       
        payload=payload,                                                                                                                                                                     
        header_signature=signature                                                                                                                                                           
    )                                                                                                                                                                                        
    return transaction                                                                                                                                                                       
                                                                     


                                                                     
def create_meta_xcert_txn(signer, key, value): 
    payload = cbor.dumps(value).hex()    
    info = {X509_COMMON_NAME:payload}
    xcert = signer.context.create_x509_certificate(info, signer.private_key, after=XCERT_AFTER_TM, before=XCERT_BEFORE_TM)

    transaction = _make_xcert_transaction(signer, XCERT_CRT_OP, key, xcert)
    return transaction                                                                                                  
                                                                     
                                                                     
def do_did_req(info,signed,signer,owner):
    did = key_to_dgt_addr(owner,pref="")
    trans = _make_xcert_transaction(signer,XCERT_CRT_OP,did,signed)
    return  trans,"did:{}:".format(did)
