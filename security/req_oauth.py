import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
#print('dir',SCRIPT_DIR)
sys.path.append(os.path.dirname(SCRIPT_DIR))
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from oauthlib.oauth2 import BackendApplicationClient
from request_oauth import OAuth2Session
from requests.auth import HTTPBasicAuth

client_id= 'gtania.spiter'
client_secret='TaniaTest.1970'

client_id= 'clientB'
client_secret='doe'
user_name = 'john'
user_pass = 'doe'
grant_type =  'password'

dgt_data = {     #'code': 'json',                                                
                 #'grant_type': 'password', #'authorization_code',
                 # 'username': 'john',
                 #'password':  'doe', 
                 'scope'  : 'calendar'                                               
                 #'redirect_uri': 'http://127.0.0.1:8003/calendar'
        }

auth = HTTPBasicAuth(client_id, client_secret)
client = BackendApplicationClient(client_id)
client.grant_type = 'password'
oauth = OAuth2Session(client=client,
                      client_id=client_id,
                      scope ='calendar' ,
                      redirect_uri='http://127.0.0.1:8003/calendar',
                      #**dgt_data
                      )


"""
dgt = OAuth2Service(
           name='clientB',
           client_id="clientB",
           client_secret="doe",
           access_token_url='http://127.0.0.1:8003/token',
           authorize_url='http://127.0.0.1:8003/o/oauth2/v2/auth',
           base_url='http://127.0.0.1:8003/userinfo/v2/'
           # user_info_url = "https://www.googleapis.com/userinfo/v2/me"
           )

dgt_params = {'redirect_uri': 'http://127.0.0.1:8003/calendar', 
                 'scope'  : 'calendar' ,            
                 'response_type': 'code'                                      
          }                                                            
                                                                       
dgt_data = {'code': 'json',                                                
        #'access_token' : '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',   
         'grant_type': 'password',#'authorization_code',
         'username': 'john',
         'password':  'doe', 
         'scope'  : 'calendar' ,                                              
        'redirect_uri': 'http://127.0.0.1:8003/calendar'
        }


"""

def main():
    token = oauth.fetch_token(token_url= 'http://127.0.0.1:8003/token', #'https://github.com/login/oauth/access_token',
                              code='json',
                              #auth=auth,
                              client_id=client_id,
                              #client_secret=client_secret,
                              username=user_name,
                              password=user_pass,
                              **dgt_data
                           )

    print('token',token)


if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    

    
