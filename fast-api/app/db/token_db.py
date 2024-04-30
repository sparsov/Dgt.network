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

import cbor
import json
from app.core.config import settings
from app.utils.logger import logger as LOGGER

#from dgt_sdk.oauth.endpoints import oauth_middleware,AioHttpOAuth2Server,OAuth2_RequestValidator,setup_oauth,AUTH_SCOPE_LIST,AUTH_USER_LIST,AUTH_CONFIG_NM
#from oauthlib import oauth2
from dgt_validator.database.indexed_database import IndexedDatabase


def deserialize_data(encoded):                
    return cbor.loads(encoded)                


def serialize_data(value):                    
    return cbor.dumps(value, sort_keys=True)  



class TokenDatabase(IndexedDatabase):
    def __init__(self, filename, serializer, deserializer,indexes=None,flag=None,_size=None,dupsort=False):
        super().__init__(filename, serializer, deserializer,indexes,flag,_size,dupsort)

                                                                                                                       
token_db = TokenDatabase(                                                                                            
        settings.TOKEN_DB_FILENAME,                                                                                             
        serialize_data,                                                                                                
        deserialize_data,                                                                                              
        indexes={'username': lambda dict: [dict['username'].encode()]},                                                    
        flag='c',                                                                                                      
        _size=settings.DEFAULT_DB_SIZE,                                                                                         
        dupsort=True                                                                                                   
        ) 

def get_token_db() -> TokenDatabase :
    return token_db
