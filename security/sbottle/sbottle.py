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
        print('validate_user',username)
        if self.users_password.get(username):
            request.user = username
            print("validate_user",username)
            return password == self.users_password.get(username)
        print("err validate_user",username)
        return False

    def validate_grant_type(self, client_id, grant_type, client, request, *args, **kwargs):
        print('validate_grant_type',grant_type)
        return grant_type in ["password",'authorization_code']

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


import bottle
from boauth2 import BottleOAuth2

#class MyOAuth2(BottleOAuth2):
#    def create_token_response(self, credentials=None):



app = bottle.Bottle()
app.auth = BottleOAuth2(app)
app.auth.initialize(oauth2.LegacyApplicationServer(OAuth2_PasswordValidator())) # BackendApplicationServer  LegacyApplicationServer


@app.get('/mail')
@app.auth.verify_request(scopes=['mail'])
def access_mail():
    return "Welcome {}, you have permissioned {} to use your mail".format(
        bottle.request.oauth["user"],
        bottle.request.oauth["client"].client_id
    )


@app.get('/calendar')
@app.auth.verify_request(scopes=['calendar'])
def access_calendar():
    return "Welcome {}, you have permissioned {} to use your calendar".format(
        bottle.request.oauth["user"],
        bottle.request.oauth["client"].client_id
    )


@app.post('/token')
@app.auth.create_token_response()
def generate_token():
    print('generate_token')
    pass


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8003)  # pragma: no cover

