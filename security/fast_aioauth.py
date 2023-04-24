#from dataclasses import dataclasses
#from aioauth_fastapi.router import get_oauth2_router
from aioauth.storage import BaseStorage
from aioauth.requests import BaseRequest, Query, Post
from aioauth.models import AuthorizationCode, Client, Token
from aioauth.config import Settings
from aioauth.server import AuthorizationServer
#from fastapi import FastAPI

#app = FastAPI()
"""
@dataclasses
class User:
    
    first_name: str
    last_name: str
"""
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
)

# Include FastAPI router with oauth2 endpoints.
#app.include_router(
#get_oauth2_router(authorization_server, settings)
#    prefix="/oauth2",
#    tags=["oauth2"],
#)
