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
from dec_common.protobuf.dec_dgt_token_pb2 import DecTokenInfo
from dec_dgt.client_cli.dec_attr import FAMILY_NAME,DEC_TARGET_GRP

def _sha512(data):
    return hashlib.sha512(data).hexdigest()
def _sha256(data):                         
    return hashlib.sha256(data).hexdigest()

 
def _get_prefix():
    return _sha512(FAMILY_NAME.encode('utf-8'))[0:6]

def _get_type_prefix(tp_space):                                  
    return _sha256(tp_space.encode('utf-8'))[0:2]

def _get_user_prefix(user):              
    return _sha256(user.encode('utf-8'))[:22]     

def _get_full_prefix(tp=None,owner=None):                                    
    fam_pref =  _get_prefix() 
    tp_pref = _get_type_prefix(DEC_TARGET_GRP if tp is None else tp)
    own_pref = _get_user_prefix(owner) if owner else ''
    return ''.join([fam_pref,tp_pref,own_pref]) 

def _get_address(name,space=None):
    prefix = _get_prefix()
    dec_address = _sha512(name.encode('utf-8'))[64:]
    return prefix + dec_address

def _get_full_addr(name,tp_space=DEC_TARGET_GRP,owner="def"):

    prefix = _get_prefix()  
    tp_prefix = _get_type_prefix(tp_space)
    usr_prefix = _get_user_prefix(owner)                         
    dec_address = _sha256(name.encode('utf-8'))[:40]     
    return ''.join([prefix,tp_prefix,usr_prefix,dec_address])  
                        
def loads_dec_token(data,name=None):
    decoded = cbor.loads(base64.b64decode(data))
    if name is not None:
        value = decoded[name]
    else:
        for key,data in decoded.items():
            name,value = key,data
            break 


    token = DecTokenInfo()       
    token.ParseFromString(value)
    try:
        dec = cbor.loads(token.dec) #if token.group_code == DEC_NAME_DEF else {} 
    except Exception as ex:
        dec = {}
    return dec
    
    
def loads_dec_entries(entries):
    results = [
                cbor.loads(base64.b64decode(entry["data"]))
                for entry in entries
            ]
    token = DecTokenInfo()  
    dres = {}                                                           
    for pair in results:                                                               
        #print('pair',pair)                                                            
        for name, value in pair.items():                                               
            token.ParseFromString(value)                                               
            try:                                                                       
                dec = cbor.loads(token.dec)# if token.group_code in DEC_TYPES else {}  
            except Exception as ex:                                                    
                dec = {} 
            dres[name]  = dec

    return dres


 

