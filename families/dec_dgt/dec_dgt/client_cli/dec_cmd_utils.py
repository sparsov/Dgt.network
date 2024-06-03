# Copyright 2024 DGT NETWORK INC © Stanislav Parsov
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
import cbor
import yaml
from dgt_signing import key_to_dgt_addr,DGT_ADDR_PREF
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import get_target_addr
from dgt_validator.gossip.fbft_topology import DGT_TOPOLOGY_SET_NM
 
def dec_req_sign(info,_signer):                                                                                         
    # sign dec request by owner                                                                                     
    # info - data relating to dec operation                                                                         
    #                                                                                                               
                                                                                                                    
    # this is header of request with owner sign                                                                     
    req_header = {                                                                                                  
            DEC_EMITTER     : _signer.get_public_key().as_hex(),                                               
            DEC_PAYLOAD     : info,                                                                                 
                                                                                                                    
    }                                                                                                               
    payload = cbor.dumps(req_header)                                                                                
    psignature = _signer.sign(payload)                                                                         
    #                                                                                                               
    #  NotaryRequest is body of request with signed header                                                          
    #                                                                                                               
    req = {                                                                                                         
            DEC_EMITTER          : req_header[DEC_EMITTER],                                                         
            DEC_NOTARY_REQ_SIGN  : psignature,                                                                      
            DEC_PAYLOAD          : payload                                                                          
        }                                                                                                           
    #ret = self._signer.verify(psign, payload,self._context.pub_from_hex(info[DEC_EMITTER]) )                       
    #if not ret:                                                                                                    
    #    print('BAD SIGN')                                                                                          
    return req  
                                                                                                    
def get_this_tips(tips,gate=DEFAULT_GATE):                                                                                                                                            
    #tips = self.get_tips(tname,op,did)                                                                                                                                                             
    for nest,val in tips.items():                                                                                                                                                                  
        if GATE_ADDR_ATTR in val :                                                                                                                                                                 
            if (gate == DEFAULT_GATE and DEFAULT_GATE in val) or nest == gate:                                                                                                                     
                val[DEFAULT_GATE] = nest                                                                                                                                                           
                return val                                                                                                                                                                         
    return 0.0 
                                                                                                                                                                                    
                                                                                                    
                                                                                                    
def get_target_opts(args,_signer):                                                                                                                                                                                                     
    target = load_json_proto(args.target_proto)                                                                            
    pkey = _signer.get_public_key().as_hex()                                                                               
    target[DEC_TARGET_PRICE] = args.price                                                                                       
    target[DEC_TARGET_INFO] = args.target if args.target else DEC_TARGET_INFO_DEF                                               
    target[DEC_TARGET_ID] = args.target_id                                                                                      
    target[DEC_TARGET_ADDR] = get_target_addr(pkey,args.target_id)  #self.get_random_addr() if False else get_target_addr(pkey,args.target_id)                    
    if args.turl:                                                                                                               
        target[DEC_TARGET_URL] = args.turl                                                                                      
    owner = key_to_dgt_addr(pkey)                                                                                               
                                                                                                                                
    target[DEC_OWNER] = owner #key_to_dgt_addr(self._signer.get_public_key().as_hex(),pref="0x")                                
    #print(type(owner),owner)                                                                                                   
    for key,val in target.items():                                                                                              
        if key not in TARGET_VISIBLE_ATTR:                                                                                      
            target[key] = key_to_dgt_addr(val,pref="")                                                                          
    if args.invoice > 0:                                                                                                        
        target[DEC_INVOICE_OP] = {DEC_CUSTOMER_KEY : None, DEC_TARGET_PRICE :args.price}                                        
    return target 
                                                                                                              
def target_info(args,tip_list,signer):                                                                                                                                                                                                                                
    # full info for target                                                                                                                                        
    info = {}                                                                                                                                                     
    tcurr = time.time()                                                                                                                                           
    target = get_target_opts(args,signer) #self.get_target_opts(args)                                                                                       
    #tip_list = self.get_tips(DEC_NAME_DEF,DEC_TARGET_OP,args.did)                                                                                                
    tips = get_this_tips(tip_list,gate=args.gate)                                                                                                                 
    info[DEC_TARGET_OP] = target                                                                                                                                  
                                                                                                                                                                  
    #info[DEC_EMITTER] = signer.get_public_key().as_hex()                                                                                                         
    info[DEC_TMSTAMP] = tcurr                                                                                                                                     
    info[DEC_TIPS_OP] = {DEC_TIPS_OP : args.tips,GATE_ADDR_ATTR :tips[GATE_ADDR_ATTR]}                                                                            
                                                                                                                                                                  
    if args.did:                                                                                                                                                  
        # refer to DID owner                                                                                                                                      
        info[DEC_DID_VAL] = args.did                                                                                                                              
        #addr = self._get_full_addr(taddr,owner=args.did)                                                                                                         
    #else:                                                                                                                                                        
    #    addr = self._get_address(taddr)                                                                                                                          
    opts = {                                                                                                                                                      
             DEC_CMD_OPTS   : info,                                                                                                                               
             DEC_TRANS_OPTS : { DEC_CMD     : DEC_TARGET_OP,                                                                                                      
                                DEC_CMD_ARG : (target[DEC_TARGET_ADDR],DEC_TARGET_GRP,args.did),                                                                  
                                DEC_CMD_DIN : [(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)]                                                                   
                              },                                                                                                                                  
             DEC_TIPS_OP : tips                                                                                                                                   
            }                                                                                                                                                     
                                                                                                                                                                  
    if args.tips > 0.0 or True:                                                                                                                                   
        # handler check To for this                                                                                                                               
        opts[DEC_TRANS_OPTS][DEC_CMD_TO] = [(target[DEC_OWNER],DEC_WALLET_GRP,args.did),(tips[GATE_ADDR_ATTR],DEC_WALLET_GRP,DEFAULT_DID)]                        
        opts[DEC_TRANS_OPTS][DEC_CMD_DIN_EXT] = (SETTINGS_NAMESPACE,DGT_TOPOLOGY_SET_NM)                                                                          
                                                                                                                                                                  
    return opts                                                                                                                                                   
