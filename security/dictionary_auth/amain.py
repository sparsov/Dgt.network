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
from aioauth import server
from aioauth.storage import BaseStorage
from aioauth.requests import BaseRequest, Query, Post
from aioauth.models import AuthorizationCode, Client, Token
from aioauth.config import Settings
from aioauth.server import AuthorizationServer

import fastapi
from aioauth_fastapi.utils import to_oauth2_request, to_fastapi_response


class User():
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name  = last_name






class Request(BaseRequest[Query, Post, User]):
    """Custom Request model"""


class Storage(BaseStorage[Token, Client, AuthorizationCode, Request]):
    """
    Storage methods must be implemented here.
    """

storage = Storage()
authorization_server = AuthorizationServer[Request, Storage](storage)

# NOTE: Redefinition of the default aioauth settings
# INSECURE_TRANSPORT must be enabled for local development only!
settings = Settings(
    INSECURE_TRANSPORT=True,
    TOKEN_EXPIRES_IN=86400
)
async def introspect(request: fastapi.Request) -> fastapi.Response:
    # Converts a fastapi.Request to an aioauth.Request.
    oauth2_request: aioauth.Request = await to_oauth2_request(request)
    # Creates the response via this function call.
    oauth2_response: aioauth.Response = await server.create_token_introspection_response(oauth2_request)
    # Converts an aioauth.Response to a fastapi.Response.
    response: fastapi.Response = await to_fastapi_response(oauth2_response)
    return response
    


#@app.post("/token")
async def token(request: fastapi.Request) -> fastapi.Response:
    # Converts a fastapi.Request to an aioauth.Request.
    print('TOKEN',request)
    oauth2_request: aioauth.Request = await to_oauth2_request(request)
    # Creates the response via this function call.
    oauth2_response: aioauth.Response = await server.create_token_response(oauth2_request)
    # Converts an aioauth.Response to a fastapi.Response.
    response: fastapi.Response = await to_fastapi_response(oauth2_response)
    return response    
#@app.post("/authorize")
async def authorize(request: fastapi.Request) -> fastapi.Response:
    # Converts a fastapi.Request to an aioauth.Request.
    print('AUTHORIZE',request,type(request))
    oauth2_request: aioauth.Request = await to_oauth2_request(request)
    # Creates the response via this function call.
    oauth2_response: aioauth.Response = await server.create_authorization_response(oauth2_request)
    # Converts an aioauth.Response to a fastapi.Response.
    response: fastapi.Response = await to_fastapi_response(oauth2_response)
    print('authorize',response)
    return response

#@app.post("/revoke")
async def revoke(request: fastapi.Request) -> fastapi.Response:
    # Converts a fastapi.Request to an aioauth.Request.
    oauth2_request: aioauth.Request = await to_oauth2_request(request)
    # Creates the response via this function call.
    oauth2_response: aioauth.Response = await server.revoke_token(oauth2_request)
    # Converts an aioauth.Response to a fastapi.Response.
    response: fastapi.Response = await to_fastapi_response(oauth2_response)
    return response




def make_app() -> web.Application:

    app = web.Application()
    app["user_map"] = user_map
    configure_handlers(app)

    # OAUTH
    router = app.router
    #print('authorization_server',dir(authorization_server))
    router.add_get("/introspect", introspect, name='introspect')
    router.add_get("/token", token, name='token')
    router.add_get("/authorize", authorize, name='authorize')
    router.add_get("/revoke", revoke, name='revoke')


    # OAUTH EOF



    # secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)

    storage = EncryptedCookieStorage(secret_key, cookie_name='API_SESSION')
    setup_session(app, storage)

    policy = SessionIdentityPolicy()
    setup_security(app, policy, DictionaryAuthorizationPolicy(user_map))

    return app


if __name__ == '__main__':
    print('START')
    web.run_app(make_app(), port=8003)
