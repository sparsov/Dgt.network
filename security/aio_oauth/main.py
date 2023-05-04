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
from aioauth2  import AioHttpOAuth2
from oauthlib import oauth2

class Client():
    client_id = None


class OAuth2_PasswordValidator(oauth2.RequestValidator):
    """dict of clients containing list of valid scopes"""
    clients_scopes = {
            "clientA": ["mail", "calendar"],
            "clientB": ["calendar"]
    }
    """dict of username containing password"""
    users_password = {
        "john": "doe",
        "foo": "bar"
    }
    tokens_info = {
    }

    def client_authentication_required(self, request, *args, **kwargs):
        print('client_authentication_required')
        return False  # Allow public clients

    def authenticate_client_id(self, client_id, request, *args, **kwargs):
        print('authenticate_client_id',client_id)
        if self.clients_scopes.get(client_id):
            request.client = Client()
            request.client.client_id = client_id
            print('OK authenticate_client_id',client_id)
            return True
        print('FALSE authenticate_client_id',client_id)
        return False

    def validate_user(self, username, password, client, request, *args, **kwargs):
        #print('validate_user',username)
        if self.users_password.get(username):
            request.user = username
            print("validate_user",username)
            return password == self.users_password.get(username)
        print("err validate_user",username)
        return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        print('validate_grant_type',grant_type)
        return grant_type in ["password",'authorization_code','client_credentials']

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        print('validate_scopes',scopes)
        #scopes= scopes.split(':')
        return all(scope in self.clients_scopes.get(client_id) for scope in scopes)

    def save_bearer_token(self, token_response, request, *args, **kwargs):
        print('save_bearer_token')
        self.tokens_info[token_response["access_token"]] = {
            "client": request.client,
            "user": request.user,
            "scopes": request.scopes
        }

    def validate_bearer_token(self, access_token, scopes_required, request):
        print('validate_bearer_token',access_token)
        info = self.tokens_info.get(access_token, None)
        if info:
            request.client = info["client"]
            request.user = info["user"]
            request.scopes = info["scopes"]
            return all(scope in request.scopes for scope in scopes_required)
        return False
@web.middleware
async def oauth_middleware(request: web.Request,handler):# : Callable[[web.Request], Awaitable[web.Response]]
    print('>>> HANDLER={}'.format(handler))
    resp = await handler(request)
    print('<<< HANDLER'.format(handler))
    return resp

def make_app() -> web.Application:
    app = web.Application(middlewares=[oauth_middleware])
    app["user_map"] = user_map
    app.auth = AioHttpOAuth2(app)
    app.auth.initialize(oauth2.LegacyApplicationServer(OAuth2_PasswordValidator()))

    configure_handlers(app)

    # secret_key must be 32 url-safe base64-encoded bytes
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)

    storage = EncryptedCookieStorage(secret_key, cookie_name='API_SESSION')
    setup_session(app, storage)

    policy = SessionIdentityPolicy()
    setup_security(app, policy, DictionaryAuthorizationPolicy(user_map))
    


    print('middlewares',app.middlewares)
    return app


if __name__ == '__main__':
    web.run_app(make_app(), port=8003)
