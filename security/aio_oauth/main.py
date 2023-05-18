import os
import sys
TOP_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
SDK=os.path.join(TOP_DIR,'sdk', 'python')
VALID=os.path.join(TOP_DIR,'validator')
sys.path.insert(0, VALID)
sys.path.insert(0, SDK)
#print('SDK',SDK)

import cbor
import base64

from aiohttp import web
from aiohttp_session import setup as setup_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from cryptography import fernet

from aiohttp_security import SessionIdentityPolicy
from aiohttp_security import setup as setup_security
from authz import DictionaryAuthorizationPolicy
from handlers import configure_handlers
from users import user_map
#
#from aioauth2  import AioHttpOAuth2,oauth_middleware,AioHttpOAuth2Server,OAuth2_RequestValidator
#from aioauth2  import setup as setup_oauth
from dgt_sdk.oauth.endpoints import oauth_middleware,AioHttpOAuth2Server,OAuth2_RequestValidator,setup_oauth,AUTH_SCOPE_LIST,AUTH_USER_LIST,AUTH_CONFIG_NM

from oauthlib import oauth2
from aiohttp_session import get_session
from dgt_validator.database.indexed_database import IndexedDatabase

TOKEN_DB_FILENAME = '/project/peer/data/tokens.lmdb'
DEFAULT_DB_SIZE= 1024*1024*1

def deserialize_data(encoded):                
    return cbor.loads(encoded)                
                                              
                                              
def serialize_data(value):                    
    return cbor.dumps(value, sort_keys=True)  



def make_app() -> web.Application:
    app = web.Application() #middlewares=[oauth_middleware])
    

    token_db = IndexedDatabase(                                                                                                
            TOKEN_DB_FILENAME,                                                                                                 
            serialize_data,                                                                                                   
            deserialize_data,                                                                                                 
            indexes={'client': lambda dict: [dict['client'].encode()]},              
            flag='c',                                                                                                         
            _size=DEFAULT_DB_SIZE,                                                                                            
            dupsort=True                                                                                                      
            )                                                                                                                 
    users = {"dgt" : "matagami2023"}

    
    #req_validator = oauth2.LegacyApplicationServer(OAuth2_RequestValidator(db=token_db,users=None,conf="/project/dgt/etc/{}".format(AUTH_CONFIG_NM)),token_expires_in=60*60*24*90)
    user_validator = OAuth2_RequestValidator(db=token_db,users=None,conf="/project/dgt/etc/{}".format(AUTH_CONFIG_NM))  
    req_validator = oauth2.LegacyApplicationServer(user_validator,token_expires_in=user_validator.token_expires_in)     
    auth = AioHttpOAuth2Server(req_validator,user_validator)

    #auth = AioHttpOAuth2(app)
    #auth.initialize(oauth2.LegacyApplicationServer(OAuth2_PasswordValidator()))
    #app.auth = auth
    
    setup_oauth(app,auth)
    configure_handlers(app)
    if False:
        app["user_map"] = user_map
        # secret_key must be 32 url-safe base64-encoded bytes
        fernet_key = fernet.Fernet.generate_key()
        secret_key = base64.urlsafe_b64decode(fernet_key)

        storage = EncryptedCookieStorage(secret_key, cookie_name='API_SESSION')
        setup_session(app, storage)

        policy = SessionIdentityPolicy()
        setup_security(app, policy, DictionaryAuthorizationPolicy(user_map))
    # oauth
    app.middlewares.append(oauth_middleware)


    print('middlewares',app.middlewares)
    return app


if __name__ == '__main__':
    web.run_app(make_app(), port=8003)
