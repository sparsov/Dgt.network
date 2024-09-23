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
import random
from dgt_sdk.protobuf.transaction_pb2 import TransactionHeader
from dgt_sdk.protobuf.transaction_pb2 import Transaction
from dgt_signing import key_to_dgt_addr,DGT_ADDR_PREF
from dec_dgt.client_cli.dec_attr import *
from dec_dgt.client_cli.dec_addr import get_target_addr,_get_full_addr,_get_address,_sha512

from dgt_validator.gossip.fbft_topology import DGT_TOPOLOGY_SET_NM
from dgt_settings.processor.utils import _make_settings_key,SETTINGS_NAMESPACE
"""
#    asset
target: - this part from client - signed his key -- any_signer.verify(psign, payload,emmiter_pub_key )
    hiden: c6a11b8b5a60a61cd996722cccddf478f38008dd2820
    invoice:
        customer: null
        target_price: 1.0
    name: DDD11112
    target_info: empty target
    target_price: 1.0
    url: url for target description
did: did:notary:30563010:000000000
timestamp: 1722061149.0916204
addr: '0x62066e09747a765c5e1746ab9320a32a964c76d54f5e'
owner: '0x5e0c2ab90c32beab70ae8f6157a328fcef9327224eb2'
tips:
    addr: '0x5e0c2ab90c32beab70ae8f6157a328fcef9327224eb2'
    this: AA.aa1
    tips: 0.1   
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
 -- user level  -make  rest api request
  {
    userkey -- signer ,
    did
    target{ all params }
   } (cbor)-> payload (userkey)-> signature
  param {
   userkey 
   signature
   payload
  } 
  -> rest api level 
  req{
   gatekey
   param.signature
   timestamp
   addr
   owner
   tips
  } 
  (cbor)-> payload (gatekey)-> signature
  freq {
   param {}
   gatekey
   req.payload
   req.signature
  }

""" 
def req2b64(req):
    req[DEC_PAYLOAD] = base64.b64encode(req[DEC_PAYLOAD]).decode('utf-8')
    return req
 
def dec_req_sign(info,signer):                                                                                         
    # sign dec request by owner                                                                                     
    # info - data relating to dec operation                                                                         
    #                                                                                                               
                                                                                                                    
    # this is header of request with owner sign                                                                     
    req_header = {                                                                                                  
            DEC_EMITTER     : signer.get_public_key().as_hex(),
            DEC_PAYLOAD     : info                                                                              
                                                                                                                    
    }                                                                                                               
    payload = cbor.dumps(req_header)                                                                                
    psignature = signer.sign(payload)                                                                         
    #                                                                                                               
    #  NotaryRequest is body of request with signed header                                                          
    #                                                                                                               
    req = {                                                                                                         
            DEC_EMITTER           : req_header[DEC_EMITTER],                                                         
            DEC_PAYLOAD_SIGNATURE : psignature,                                                                      
            DEC_PAYLOAD           : payload                                                                          
        }                                                                                                           
    #ret = self._signer.verify(psignature, payload,self._context.pub_from_hex(info[DEC_EMITTER]) )                       
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
                                                                                                                                                                                    
def get_all_target_opts(args):                                                                                                                                                                                                                  
    target = load_json_proto(args.target_proto)                                                                                                                                                                                                    
    target[DEC_TARGET_PRICE] = args.price                                                                                                                                                                                                                 
    target[DEC_TARGET_INFO] = args.target if args.target else DEC_TARGET_INFO_DEF                                                                                                                                                                         
    target[DEC_TARGET_ID] = args.target_id 
    target[DEC_TIPS_OP] = args.tips                                                                                                                                                                                                               
    #target[DEC_TARGET_ADDR] = get_target_addr(pkey,args.target_id)  #self.get_random_addr() if False else get_target_addr(pkey,args.target_id)                                                                                                            
    if args.turl:                                                                                                                                                                                                                                         
        target[DEC_TARGET_URL] = args.turl                                                                                                                                                                                                                
    #owner = key_to_dgt_addr(pkey)                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                          
    #target[DEC_OWNER] = owner #key_to_dgt_addr(self._signer.get_public_key().as_hex(),pref="0x")                                                                                                                                                          
    #print(type(owner),owner)                                                                                                                                                                                                                             
    for key,val in target.items():                                                                                                                                                                                                                        
        if key not in TARGET_VISIBLE_ATTR:                                                                                                                                                                                                                
            target[key] = key_to_dgt_addr(val,pref="") 
    target[DEC_IS_INVOICE]  =  args.invoice > 0 
    #target[DEC_DID_VAL] = args.did if args.did else DEFAULT_DID                                                                                                                                                                                              
    #if args.invoice > 0:                                                                                                                                                                                                                                  
    #    target[DEC_INVOICE_OP] = {DEC_CUSTOMER_KEY : None, DEC_TARGET_PRICE :args.price}                                                                                                                                                                  
    return target                                                                                                                                                                                                                                         
                                                                                                    
                                                                                                    
                                                                                                    
                                                                                                    
def get_target_opts(args,signer):                                                                                                                                                                                                     
    target = load_json_proto(args.target_proto)                                                                            
    target[DEC_TARGET_PRICE] = args.price                                                                                       
    target[DEC_TARGET_INFO] = args.target if args.target else DEC_TARGET_INFO_DEF                                               
    target[DEC_TARGET_ID] = args.target_id                                                                                      
    
    if args.turl:                                                                                                               
        target[DEC_TARGET_URL] = args.turl                                                                                      

    for key,val in target.items():                                                                                              
        if key not in TARGET_VISIBLE_ATTR:                                                                                      
            target[key] = key_to_dgt_addr(val,pref="")                                                                          

    target[DEC_INVOICE_OP] = args.invoice > 0
    target[DEC_ADDR_IND] = 0
    target[DEC_WALLETS_OWNERS] = [signer.get_public_key().as_hex()]
    return target 
                                                                                                              
def gate_req_sign(opts,req,nsigner):                                                                                                                                                                                                      
    # this is header of gate signed request 
    ukey = req[DEC_EMITTER]
    owner = key_to_dgt_addr(ukey)                                                                                                                                                                                              
    gate_hdr = {                                                                                                                                                                                                                          
                DEC_SIGNER_PUBKEY      : nsigner.get_public_key().as_hex(),                                                                                                                                                                    
                DEC_PAYLOAD_SIGNATURE  : req[DEC_PAYLOAD_SIGNATURE] ,
                DEC_TARGET_ADDR        : get_target_addr(req[DEC_EMITTER],opts[DEC_TARGET_ID]),
                DEC_OWNER              : owner                                                                                                                                                                            
             }                                                                                                                                                                                                                              
    hpayload = cbor.dumps(gate_hdr)                                                                                                                                                                                                       
    hsignature = nsigner.sign(hpayload)                                                                                                                                                                                                     
    # this is user request signed twice - user and gate                                                                                                                                                                                   
    gate_request_sign = {                                                                                                                                                                                                                 
                            DEC_HEADER_PAYLOAD     : hpayload, # keep signature for user signed request                                                                                                                                         
                            DEC_PAYLOAD_SIGNATURE  : hsignature,                                                                                                                                                                                
                            DEC_PAYLOAD            : req[DEC_PAYLOAD] # keep user public key  and target params                                                                                                                                                 
                          }                                                                                                                                                                                                                 
    return gate_request_sign,gate_hdr                                                                                                                                                                                                              
                                                                                                              
                                                                                                              
                                                                                                              
                                                                                                              
                                                                                                              
                                                                                                              
def target_info(target,tip_list,signer):                                                                                                                                                                                                                                
    # full info for target                                                                                                                                        
    info = {}                                                                                                                                                     
    tcurr = time.time()  
    #proto = load_json_proto(args.target_proto)                                                                                                                                         
    #target = get_target_opts(args,proto,signer) #self.get_target_opts(args)                                                                                       
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
                                                                                                                                                 
                                                                                                                                                 
def dec_gate_sign(req,extra,nsigner):
    gate_hdr = {                                                                                                                              
                DEC_NOTARY_KEY       : nsigner.get_public_key().as_hex(),      #DEC_SIGNER_PUBKEY                                             
                DEC_NOTARY_REQ_SIGN  : req[DEC_PAYLOAD_SIGNATURE] ,            #DEC_PAYLOAD_SIGNATURE                                         
                DEC_PAYLOAD          : extra                                                                                                   
             }                                                                                                                                
    hpayload = cbor.dumps(gate_hdr)                                                                                                           
    hsignature = nsigner.sign(hpayload)                                                                                                       
    # this is user request signed twice - user and gate                                                                                       
    gate_request_sign = {                                                                                                                     
                            DEC_HEADER_PAYLOAD     : hpayload, # keep signature for user signed request                                       
                            DEC_HEADER_SIGN        : hsignature,                                                                              
                            DEC_PAYLOAD            : req[DEC_PAYLOAD] # keep user public key  and target params                               
                          }                                                                                                                   
    # trans params 
    return gate_request_sign,gate_hdr                                                                                                                           


                                                                                                                                                 
                                                                                                                                                 
def do_signed_target_req(info,signer,did=DEFAULT_DID):
    payload = {                               
                DEC_TARGET_OP   : info,       
                DEC_DID_VAL     : did         
              }                               


    return dec_req_sign(payload,signer)

def do_target_req(info,req,tips,nsigner,did=DEFAULT_DID):
    """do full request
    freq {                  
     param {}               
     gatekey                
     req.payload            
     req.signature          
    }                       
    """
    
    ukey =  info[DEC_WALLETS_OWNERS][info[DEC_ADDR_IND]] if DEC_WALLETS_OWNERS in info else  req[DEC_EMITTER]                                                                                           
    owner = key_to_dgt_addr(ukey)  
    print("owner",owner,key_to_dgt_addr(req[DEC_EMITTER]))
    addr  = get_target_addr(ukey,info[DEC_TARGET_ID]) 
    if info[DEC_TIPS_OP] < tips[DEC_TIPS_OP]:
        tips[DEC_TIPS_OP] = 0.0
    extra = {  # extra params                                           
                 DEC_TMSTAMP            : time.time(),                  
                 DEC_TARGET_ADDR        : addr,                         
                 DEC_OWNER              : owner ,                       
                 DEC_TIPS_OP            : tips                          
              }                                                         
    # this is user request signed twice - user and gate                                                                            
    gate_request_sign,gate_hdr = dec_gate_sign(req, extra, nsigner) 
    # trans params  
    topts = { DEC_CMD     : DEC_TARGET_OP,                                                                                                  
             DEC_CMD_ARG : (addr,DEC_TARGET_GRP,did),                                                              
             DEC_CMD_DIN : [(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)]                                                               
            }                                                                                                                              
    if True:                                                                                                            
         # handler check To for this                                                                                                       
         topts[DEC_CMD_TO] = [(owner,DEC_WALLET_GRP,did),(tips[GATE_ADDR_ATTR],DEC_WALLET_GRP,DEFAULT_DID)]                
         topts[DEC_CMD_DIN_EXT] = (SETTINGS_NAMESPACE,DGT_TOPOLOGY_SET_NM)                                                                  
    
    
    
                                                                                                          
    return gate_request_sign,gate_hdr,topts,addr                                                                                              



def make_dec_transaction(_signer,verb, name, value, to=None,din=None,din_ext=None):                                                                  
    val = {                                                                                                                                   
        DEC_CMD    : verb,                                                                          
        DEC_CMD_ARG: name,                                                                                                                             
        DEC_CMD_VAL: value, # sign twice                                                                                                                            
    }                                                                                                                                        
    if to is not None:  
        if not isinstance(to,list):    
            to = [to]  
        #tval = to[0]                                                                                                               
        val[DEC_CMD_TO] = to #tval[0] if isinstance(tval,tuple) else tval                                                                                                                      

    hex_pubkey =  _signer.get_public_key().as_hex()                                                                                                                                       
    sign_val = {} 

    # Construct the address                                                                                                                   
    address = _get_full_addr(name[0],name[1],name[2])#_get_address(name) 
    #print('NAME',address)                                                                                                        
    inputs = [address]                                                                                                                        
    outputs = [address]                                                                                                                       
    if to is not None: 
        for tval in to:
            address_to = _get_full_addr(tval[0],tval[1],tval[2]) if isinstance(tval,tuple) else _get_address(tval)
            inputs.append(address_to)                                                                                                             
            outputs.append(address_to) 
            #print("TO",tval[0],address_to)
    dinputs = []                                                                                                            
    if din is not None:                                                                                                                       
        for ain in (din if isinstance(din,list) else [din]):                                                                                                                   
            address_in = _get_full_addr(ain[0],ain[1],ain[2]) if isinstance(ain,tuple) else _get_address(ain)                                                                                               
            inputs.append(address_in) 
            dinputs.append((FAMILY_NAME,ain[0],ain[1],ain[2])) #(FAMILY_NAME,ain[0] if isinstance(ain,tuple) else ain))

    if din_ext is not None:
        # external family 
        dinputs_ext = din_ext if isinstance(din_ext,list) else [din_ext]
        for fam,ain in dinputs_ext:
            if fam == SETTINGS_NAMESPACE:
                address_in = _make_settings_key(ain)
                inputs.append(address_in)
                dinputs.append((fam,ain))
    # input list
    val[DATTR_INPUTS] = dinputs

    #print("in={} out={} din={}".format(inputs,outputs,dinputs))
    payload = cbor.dumps(val)
    psign = _signer.sign(payload) # for fool notary mode this is notary node sign 
    sign_val[DEC_SIGNATURE] =  psign
    sign_val[DEC_PUBKEY]    = hex_pubkey
    sign_val[DATTR_VAL]     =  payload                                                                                         
    spayload = cbor.dumps(sign_val)  

    #print("PSIGN={}".format(psign))                                                                                                               
    header = TransactionHeader(                                                                                                               
        signer_public_key=hex_pubkey,                                                                             
        family_name=FAMILY_NAME,                                                                                                              
        family_version=FAMILY_VERSION,                                                                                                        
        inputs=inputs,                                                                                                                        
        outputs=outputs,                                                                                                                      
        dependencies=[],                                                                                                                      
        payload_sha512=_sha512(spayload),                                                                                                      
        batcher_public_key=hex_pubkey,                                                                            
        nonce=hex(random.randint(0, 2**64))                                                                                                   
    ).SerializeToString()                                                                                                                     

    signature = _signer.sign(header)                                                                                                     

    transaction = Transaction(                                                                                                                
        header=header,                                                                                                                        
        payload=spayload,                                                                                                                      
        header_signature=signature                                                                                                            
    ) 
    return transaction                                                                                                                                        

                                                                                              

def do_signed_wallet_req(opts,did,signer):                                                                                                                  
    # load default options                                                                                                                             
    #opts = load_json_proto(args.opts_proto)                                                                                                       
    sign_min = opts[DEC_SIGN_MIN] if DEC_SIGN_MIN in opts else 1
    addr_ind = opts[DEC_ADDR_IND] if DEC_ADDR_IND in opts else 0                                                                                                                                            
    signs = [] 
    if DEC_WALLETS_OWNERS not in opts:
        opts[DEC_WALLETS_OWNERS] = [signer.get_public_key().as_hex()]
    pubkey = opts[DEC_WALLETS_OWNERS][addr_ind]                                                                                                                                  
    for sign in opts[DEC_WALLETS_OWNERS]:                                                                                                              
        signs.append(key_to_dgt_addr(sign))   #self.get_pub_key(signer)                                                                               
                                                                                                                                                   
    opts[DEC_WALLETS_OWNERS] = { DEC_ESIGN_NUM : sign_min,DEC_ESIGNERS : signs}                                     
    #print("DEC.wallet opts{}".format(opts))
    payload = {                               
                DEC_WALLET_OP   : opts,       
                DEC_DID_VAL     : did         
              }   

    

    return dec_req_sign(payload,signer),pubkey                                                                                                          
   

def do_wallet_req(wallet,req,pubkey,nsigner,did=DEFAULT_DID):                                                                                           
    waddr = key_to_dgt_addr(pubkey)
    extra = { 
            #DEC_WALLET_OP   : wallet, 
            DEC_TMSTAMP     : time.time(),
            DEC_WALLET_ADDR : waddr
            }
    gate_request_sign,_ = dec_gate_sign(req, extra, nsigner)
    #info[DEC_EMITTER] = signer.get_public_key().as_hex()                            
    din = [(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)]                          
    #addr = self._get_full_addr(waddr,tp_space=DEC_WALLET_GRP,owner=args.did)        
    topts =  { DEC_CMD    : DEC_WALLET_OP,                          
               DEC_CMD_ARG: (waddr,DEC_WALLET_GRP,did),        
               DEC_CMD_DIN: din                                     
             }                                                      
            
    return gate_request_sign,topts,waddr  
                                                                  
                                                                  
def do_signed_invoice_req(opts,did,signer):
    #
    payload = {                                       
                DEC_INVOICE_OP   : opts,               
                DEC_DID_VAL     : did                 
              }                                       
                                                      
                                                      
                                                      
    return dec_req_sign(payload,signer),opts[DEC_WALLETS_OWNERS]      



def do_invoice_req(invoice,req,pubkey,nsigner,did=DEFAULT_DID):
    
    target = get_target_addr(pubkey,invoice[DEC_TARGET])                                              
    extra = {                                                                    
            DEC_TMSTAMP     : time.time(),                                       

            }                                                                    
    gate_request_sign,_ = dec_gate_sign(req, extra, nsigner)                     
    #info[DEC_EMITTER] = signer.get_public_key().as_hex()                        
    din = [(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)] 
    if invoice[DEC_CUSTOMER_KEY] is not None:             
        din.append(invoice[DEC_CUSTOMER_KEY]) 
    
                         
    #addr = self._get_full_addr(waddr,tp_space=DEC_WALLET_GRP,owner=args.did)    
    topts =  { DEC_CMD    : DEC_INVOICE_OP,                                       
               DEC_CMD_ARG:  (target,DEC_TARGET_GRP,did),                          
               DEC_CMD_DIN: din                                                  
             }                                                                   
                                                                                 
    return gate_request_sign,topts,target  
                                       
def do_signed_pay_req(opts,did,signer):
    # pay request 
    payload = {                                                                                            
                DEC_PAY_OP   : opts,                           
                DEC_DID_VAL  : did                              
              }                                                    
                                                                   
                                                                   
    
    return dec_req_sign(payload,signer),opts[DEC_CUSTOMER_KEY] 

def do_pay_req(pinfo,req,pubkey,nsigner,did=DEFAULT_DID):
    extra = {                                                 
            DEC_TMSTAMP     : time.time(),                    
                                                              
            }                                                 
    gate_request_sign,_ = dec_gate_sign(req, extra, nsigner)
    odid = pinfo[DEC_DID_VAL] if DEC_DID_VAL in pinfo and pinfo[DEC_DID_VAL] else DEFAULT_DID
    to = [(pinfo[DEC_OWNER],DEC_WALLET_GRP,odid)] 
    to.append((pinfo[DEC_TARGET_INFO],DEC_TARGET_GRP,did))    # args.didto                       
    if DEC_TRANS_ID in pinfo and pinfo[DEC_TRANS_ID]:                                                                
        to.append((DEC_TRANS_KEY.format(pinfo[DEC_TRANS_ID]),DEC_EMISSION_GRP,odid))                                                    
    din = [(DEC_EMISSION_KEY,DEC_EMISSION_GRP,DEFAULT_DID)]


    faddr = (pinfo[DEC_CUSTOMER_KEY],DEC_WALLET_GRP,did)
    
    
    topts =  { DEC_CMD    : DEC_PAY_OP,                   
               DEC_CMD_ARG:  faddr, 
               DEC_CMD_TO : to,  
               DEC_CMD_DIN: din                             
             }                                              
                                                            
    return gate_request_sign,topts                   
