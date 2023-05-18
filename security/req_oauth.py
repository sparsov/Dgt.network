import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOP_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
SDK=os.path.join(TOP_DIR,'sdk', 'python')
sys.path.insert(0, SDK)






print('dir',SCRIPT_DIR,SDK)
sys.path.append(os.path.dirname(SCRIPT_DIR))
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from oauthlib.oauth2 import BackendApplicationClient
#from request_oauth import OAuth2Session
from dgt_sdk.oauth.requests import OAuth2Session
from requests.auth import HTTPBasicAuth

client_id= 'gtania.spiter'
client_secret='TaniaTest.1970'

client_id     = 'clientC'
client_secret = 'doe'
user_name     = 'john'
user_pass     = 'doe'
grant_type    = 'password'
scopes        = [ "calendar"
                  #,"mail"
                 #'status', 'calendar', 'state', 'show', 'trans'
                 ]  #'calendar'

dgt_data = {     #'code': 'json',                                                
                 #'grant_type': 'password', #'authorization_code',
                 # 'username': 'john',
                 #'password':  'doe', 
                 'scope'  :  scopes                                              
                 #'redirect_uri': 'http://127.0.0.1:8003/calendar'
        }

#auth = HTTPBasicAuth(client_id, client_secret)


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




"""
tok1 = {'access_token': '46GGb6AQoYoNfq9CcDwbL0r8bE5cMM', 'expires_in': 3600, 'token_type': 'Bearer',
       'scope': ['calendar', 'mail'], 'refresh_token': 'uG5KiJf23CU9sqZvHmrK26Pq4tDC6p', 'expires_at': 1683384237.985666
       }
tok = {'access_token':  'xWU7lqnM18O3hRZUfe9SfnlmxAa05G'# '46GGb6AQoYoNfq9CcDwbL0r8bE5cMM',
       # 'expires_in': 3600, 'token_type': 'Bearer',                                                   
       #'scope': ['calendar', 'mail'], 
       #'refresh_token': 'uG5KiJf23CU9sqZvHmrK26Pq4tDC6p', 'expires_at': 1683384237.985666                               
       }                                                                                                                                               

def main():
    reqmode = True
    client = BackendApplicationClient(client_id)                                                
    client.grant_type = 'password' #'authorization_code' #'password'                            
    oauth = OAuth2Session(client=None, #client if reqmode else None,                                                        
                          client_id=client_id if reqmode else None,                                                  
                          scope =scopes if reqmode else None, 
                          token = tok if not reqmode else None, 
                          grant_type = 'password',                                                     
                          #redirect_uri='http://127.0.0.1:8003/calendar',                       
                          #**dgt_data                                                           
                          )                                                                     


    if reqmode:
        token = oauth.fetch_token(token_url= 'http://api-dgt-c1-1:8108/token',#'http://127.0.0.1:8003/token', #'https://github.com/login/oauth/access_token',
                                  code='json',
                                  #auth=auth,
                                  #client_id=client_id,
                                  #client_secret=client_secret,
                                  username=user_name,
                                  password=user_pass,
                                  **dgt_data
                               )

        print('token',token)
    #return
    ret = oauth.request('GET', 'http://api-dgt-c1-1:8108/peer')#'http://127.0.0.1:8003/calendar')
    print('cal:ret',ret,ret.content)
    #return
    ret = oauth.request('GET', 'http://127.0.0.1:8003/mail') 
    if ret.status_code == 200:
        print('mail:ret',ret,ret.content)  
    else:
        print('ret',ret.status_code)
    #ret = oauth.request('GET', 'http://127.0.0.1:8003/public')
    ret = oauth.get( 'http://127.0.0.1:8003/public')
    print('public',ret,ret.content)






if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    

    
