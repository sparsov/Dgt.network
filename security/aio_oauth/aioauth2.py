import functools
import json
from oauthlib.common import add_params_to_uri
from oauthlib.oauth2 import FatalClientError
from oauthlib.oauth2 import OAuth2Error
from aiohttp import web,BasicAuth,hdrs
from aiohttp_session import get_session
import requests
import logging

log = logging.getLogger(__name__)


async def extract_params(arequest):
    """Extract request informations to oauthlib implementation.
    HTTP Authentication Basic is read but overloaded by payload, if any.

    returns tuple of :
    - url
    - method
    - body (or dict)
    - headers (dict)
    """
    #auth = BasicAuth('')
    # this returns (None, None) for Bearer Token.
    #body = await arequest.text()
    forms = await arequest.post()
    #print("query",arequest.query)
    """
    for i,v in arequest.query.items():
        print("q[{}]={}".format(i,v))
    for i,v in forms.items(): 
        print("F[{}]={}".format(i,v)) 
    """ 
    username,password = None,None
    auth_header = arequest.headers.get(hdrs.AUTHORIZATION)
    if auth_header is not None:
        #print('Authorization={}'.format(arequest.headers['Authorization']))
        try:
            
            rauth = BasicAuth.decode(auth_header)
            #print('rauth={}'.format(auth_header))
            username,password = rauth.login,rauth.password
        except ValueError:
            pass
    
    print('username={}, password=/{}/ h={}'.format(username, password,dict(arequest.headers)))
    if "application/x-www-form-urlencoded" in arequest.content_type:
        client = {}
        if username is not None:
            client["client_id"] = username
        if password is not None:
            client["client_secret"] = password
        print('forms',dict(client, **forms),type(arequest.url))
        return \
            str(arequest.url), \
            arequest.method, \
            dict(client, **forms), \
            dict(arequest.headers)

    basic_auth = {}
    body = arequest.body if arequest.body_exists else None

    # TODO: Remove HACK of using body for GET requests. Use commented code below
    # once https://github.com/oauthlib/oauthlib/issues/609 is fixed.
    if username is not None:
        print('username={}, password={}'.format(username, password))
        basic_auth = {
            "Authorization": requests.auth._basic_auth_str(username, password)
        }
        body = dict(client_id=username, client_secret=password)
    print('body',dict(arequest.headers, **basic_auth))
    return \
        str(arequest.url), \
        arequest.method, \
        body, \
        dict(arequest.headers, **basic_auth)


def add_params_to_request(arequest, params):
    try:
        arequest.oauth
    except AttributeError:
        arequest.oauth = {}
    print('add_params={}'.format(params))
    if params:
        for k, v in params.items():
            arequest.oauth[k] = v


def set_response(arequest, status, headers, dbody, force_json=False):
    """Set status/headers/body into response.

    Headers is a dict
    Body is ideally a JSON string (not dict).
    """
    if not isinstance(headers, dict):
        raise TypeError("a dict-like object is required, not {0}".format(type(headers)))
    if not dbody:                                                                     
        return                                                                       
                                                                                     
    if not isinstance(dbody, str):                                                    
        raise TypeError("a str-like object is required, not {0}".format(type(dbody))) 
    content_type = None
    charset=None
    try:                                                                                                            
        values = json.loads(dbody)                                                                                   
    except json.decoder.JSONDecodeError:                                                                            
        # consider body as string but not JSON, we stop here.                                                       
        body = dbody                                                                                 
        log.debug("Body Bottle response body created as is: %r",body)                              
    else:  # consider body as JSON                                                                                  
        # request want a json as response  
        rheaders = dict(arequest.headers)                                                                         
        if force_json is True or (                                                                                  
                "Accept" in rheaders and                                                              
                "application/json" in rheaders["Accept"]):                                            
            content_type = "application/json" 
            charset= "UTF-8"                                    
            body = dbody                                                                             
            log.debug("Body Bottle response body created as json: %r",body)                        
        else:                                                                                                       
            from urllib.parse import quote                                                                          
                                                                                                                    
            content_type = "application/x-www-form-urlencoded" 
            charset = "UTF-8"                    
            body = "&".join([                                                                       
                "{0}={1}".format(                                                                                   
                    quote(k) if isinstance(k, str) else k,                                                          
                    quote(v) if isinstance(v, str) else v                                                           
                ) for k, v in values.items()                                                                        
            ])                                                                                                      
            log.debug("Body Bottle response body created as form-urlencoded: %r", body)             




    print('content_type={} body={}'.format(content_type,body))
    return web.Response(
                status=status,
                content_type=content_type if "Content-Type" not in headers else None,
                #charset=charset,
                headers=headers,
                body=body)
    


class AioHttpOAuth2(object):
    def __init__(self, web_app):
        self._web_app = web_app
        self._error_uri = None
        self._oauthlib = None

    def initialize(self, oauthlib_server, error_uri=None):
        self._error_uri = error_uri
        self._oauthlib = oauthlib_server

    def create_metadata_response(self):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                uri, http_method, body, headers = extract_params(request)

                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_metadata_response(
                        uri, http_method, body, headers
                    )
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code
                resp = set_response(request, resp_status,resp_headers, resp_body, force_json=True)

                func_response = f()
                if func_response:
                    return func_response
                return resp
            return wrapper
        return decorator

    def create_token_response(self, credentials=None):
        def decorator(f):
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                session = await get_session(request)
                print('SESSION..',session)
                session['token'] = True
                print('SESSION',session)
                # Get any additional creds
                try:
                    credentials_extra = credentials(request)
                except TypeError:
                    credentials_extra = credentials

                print('args',args,type(request),'kwargs',kwargs)
                uri, http_method, body, headers = await extract_params(request) 
                print("create_token_response:url={} metod={} body={} head={} cred={}".format(uri, http_method, body, headers,credentials_extra))
                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_token_response(
                        uri, http_method, body, headers, credentials_extra
                    )
                    print("create_token_response: cred={} rhead={} rbody={} rst={}".format(credentials_extra,resp_headers, resp_body, resp_status))
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code
                print('st={} head={} b={}'.format(type(resp_status),type(resp_headers),type(resp_body)))
                resp = set_response(request, resp_status,resp_headers, resp_body)
                print('func_response',f)
                func_response = f(request) # (*args, **kwargs)
                if func_response:
                    return func_response
                print("create_token_response 2",resp)
                return resp
            return wrapper
        return decorator

    def verify_request(self, scopes=None):
        def decorator(f):
            @functools.wraps(f)
            async def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                # Get the list of scopes
                try:
                    scopes_list = scopes(request)
                except TypeError:
                    scopes_list = scopes

                uri, http_method, body, headers = await extract_params(request)
                print('uri={}, method={}, body={}, headers={}'.format(uri, http_method, body, headers))
                valid, req = self._oauthlib.verify_request(uri, http_method, body, headers, scopes_list)
                print('valid={}, req={}'.format(valid, req))
                # For convenient parameter access in the view
                add_params_to_request(request, {
                    'client': req.client,
                    'user': req.user,
                    'scopes': req.scopes
                })
                if valid:
                    return f(request) #*args, **kwargs)

                # Framework specific HTTP 403
                resp = web.Response(
                                status=403,
                                text= "Permission denied"
                                )
                return resp
            return wrapper
        return decorator

    def create_introspect_response(self):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                uri, http_method, body, headers = extract_params(request)

                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_introspect_response(
                        uri, http_method, body, headers
                    )
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code
                resp = set_response(request, resp_status, resp_headers,resp_body, force_json=True)

                func_response = f(request) #*args, **kwargs)
                if func_response:
                    return func_response
                return resp
            return wrapper
        return decorator

    def create_authorization_response(self):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                uri, http_method, body, headers = extract_params(request)
                # maybe request.params is request.query
                scope = request.params.get('scope', '').split(' ')

                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_authorization_response(
                        uri, http_method=http_method, body=body, headers=headers, scopes=scope
                    )
                except FatalClientError as e:
                    if self._error_uri:
                        raise web.Response(#bottle.HTTPResponse(
                            status=302, headers={"Location": add_params_to_uri(
                            self._error_uri, {'error': e.error, 'error_description': e.description}
                            )})
                    raise e
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code
                resp = set_response(request, resp_status, resp_headers, resp_body)

                func_response = f(request) #*args, **kwargs)
                if func_response:
                    return func_response
                return resp
            return wrapper
        return decorator

    def create_revocation_response(self):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                uri, http_method, body, headers = extract_params(request)

                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_revocation_response(
                        uri, http_method=http_method, body=body, headers=headers
                    )
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code

                resp = set_response(request, resp_status, resp_headers, resp_body)

                func_response = f(request) #*args, **kwargs)
                if func_response:
                    return func_response
                return resp
            return wrapper
        return decorator

    def create_userinfo_response(self):
        def decorator(f):
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                assert self._oauthlib, "AioHttpOAuth2 not initialized with OAuthLib"
                request = args[0]
                uri, http_method, body, headers = extract_params(request)

                try:
                    resp_headers, resp_body, resp_status = self._oauthlib.create_userinfo_response(
                        uri, http_method=http_method, body=body, headers=headers
                    )
                except OAuth2Error as e:
                    resp_headers, resp_body, resp_status = e.headers, e.json, e.status_code

                resp = set_response(request, resp_status, resp_headers, resp_body, force_json=True)

                func_response = f(request) #*args, **kwargs)
                if func_response:
                    return func_response
                return resp
            return wrapper
        return decorator
