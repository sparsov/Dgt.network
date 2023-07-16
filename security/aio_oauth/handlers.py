from textwrap import dedent
from typing import Dict, NoReturn, Optional

from aiohttp import web

from aiohttp_security import (authorized_userid, check_authorized, check_permission, forget,remember)
from authz import check_credentials
from users import User
#from aioauth2  import create_token_response,verify_request
from dgt_sdk.oauth.endpoints import create_token_response,verify_request

index_template = dedent("""
    <!doctype html>
        <head></head>
        <body>
            <p>{message}</p>
            <form action="/login" method="post">
                Login:
                <input type="text" name="username">
                Password:
                <input type="password" name="password">
                <input type="submit" value="Login">
            </form>
            <a href="/logout">Logout</a>
        </body>
""")

class DgtRouteHandler:
    def __init__(self, auth):  
        self._auth = auth                                     

    #@self._auth.create_token_response()                                        
    def generate_token(self,request :web.Request) : 
        print('generate_token')                                              



"""

async def index(request: web.Request) -> web.Response:
    username = await authorized_userid(request)
    if username:
        template = index_template.format(
            message='Hello, {username}!'.format(username=username))
    else:
        template = index_template.format(message='You need to login')
    return web.Response(
        text=template,
        content_type='text/html',
    )


async def login(request: web.Request) -> NoReturn:
    user_map: Dict[Optional[str], User] = request.app["user_map"]
    invalid_response = web.HTTPUnauthorized(body="Invalid username / password combination")
    form = await request.post()
    username = form.get('username')
    password = form.get('password')

    if not (isinstance(username, str) and isinstance(password, str)):
        raise invalid_response

    verified = await check_credentials(user_map, username, password)
    if verified:
        response = web.HTTPFound("/")
        await remember(request, response, username)
        raise response

    raise invalid_response


async def logout(request: web.Request) -> web.Response:
    await check_authorized(request)
    response = web.Response(
        text='You have been logged out',
        content_type='text/html',
    )
    await forget(request, response)
    return response


async def internal_page(request: web.Request) -> web.Response:
    #await check_permission(request, 'public')
    await verify_request(request,scopes=['calendar'])
    response = web.Response(
        text='This page is visible for all registered users',
        content_type='text/html',
    )
    return response


async def protected_page(request: web.Request) -> web.Response:
    await check_permission(request, 'protected')
    response = web.Response(
        text='You are on protected page',
        content_type='text/html',
    )
    return response
"""

async def generate_token(request :web.Request) -> web.Response:
    #resp = await create_token_response(request)
    print('generate_token') 
    #return resp              


async def access_calendar(request :web.Request): 
    #await verify_request(request,scopes=['calendar'])                                                        
    response = web.Response(       # "user"   "client"                                             
        text="Welcome {}, you have permissioned {} to use your calendar".format(request.get("user"),request.get("scopes")),     
        content_type='text/html',                                                                  
    )                                                                                              
    return response  
                                                                              
async def access_mail(request :web.Request):                                                              
    #await verify_request(request,scopes=['mail'])                                                         
    response = web.Response(       # "user"   "client"                                                        
        text="Welcome {}, you have permissioned {} to use your mail".format(request.get("user"),request.get("scopes")),                
        content_type='text/html',                                                                             
    )                                                                                                         
    return response                                                                                           

async def internal_page(request: web.Request) -> web.Response:                     
    #await check_permission(request, 'public')                                     
    #await verify_request(request,scopes=['calendar'])                              
    response = web.Response(                                                       
        text='This page is visible for all registered users',                      
        content_type='text/html',                                                  
    )                                                                              
    return response                                                                





def configure_handlers(app: web.Application) -> None:
    """
    @app.auth.create_token_response()
    def generate_token(request :web.Request) : #(*args, **kwargs):
        print('generate_token')
        
    # access control
    
    @app.auth.verify_request(scopes=['calendar'])                                                         
    def access_calendar(request :web.Request):   
        response = web.Response(       # "user"   "client"                        
            text="Welcome {}, you have permissioned {} to use your calendar".format('joe','pass'),
            content_type='text/html',                            
        )                                                        
        return response  
                                            
    @app.auth.verify_request(scopes=['mail'])                                                         
    def access_mail(request :web.Request):                                                            
        response = web.Response(       # "user"   "client"                                                
            text="Welcome {}, you have permissioned {} to use your mail".format('joe','pass'),        
            content_type='text/html',                                                                     
        )                                                                                                 
        return response  
    """                                                                                 
    #handl = DgtRouteHandler(app.auth)
    router = app.router
    if False:
        router.add_get('/', index, name='index')
        router.add_post('/login', login, name='login')
        router.add_get('/logout', logout, name='logout')
        router.add_get('/public', internal_page, name='public')
        router.add_get('/protected', protected_page, name='protected')

    router.add_post('/token', generate_token, name='token')
    router.add_get('/calendar', access_calendar, name='calendar')
    router.add_get('/mail', access_mail, name='mail')
    router.add_get('/public', internal_page, name='public')