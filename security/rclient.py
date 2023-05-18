from rauth import OAuth2Session #,OAuth2Service
from rauth.service import OAuth2Service
import json

def decode_json(payload):
    print('payload',payload)
    return json.loads(payload.decode('utf-8'))

gitservice = OAuth2Service(
           name='github',
           client_id='sparsov',
           client_secret='Ghbdtnueuk.1964',
           access_token_url='https://github.com/login/oauth/access_token',
           authorize_url='https://github.com/login/oauth/authorize',
           base_url='https://api.github.com'
           # user_info_url = "https://api.github.com/user"
           )

params = {'redirect_uri': 'https://api.github.com/user',
          'response_type': 'code'
          }

data = {'code': 'json',
        'access_token' : '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',
        'grant_type': 'authorization_code',
        'redirect_uri': 'https://api.github.com/user'}
#  google
CID= 'gtania.spiter'
CSE='TaniaTest.1970'
CID= 'stan.parsov' 
CSE='Ghbdtnueuk.1964' 
googleserv = OAuth2Service(
           name='google',
           client_id=CID,
           client_secret=CSE,
           access_token_url='https://oauth2.googleapis.com/token',
           authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
           base_url='https://www.googleapis.com/userinfo/v2/'
           # user_info_url = "https://www.googleapis.com/userinfo/v2/me"
           )
goog_params = {'redirect_uri': 'https://www.googleapis.com/userinfo/v2/me', 
                 'scope'  : 'user:email' ,            
                 'response_type': 'code'                                      
          }                                                            
                                                                       
goog_data = {'code': 'foobar',                                                
        #'access_token' : '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',   
        'grant_type': 'password',#'authorization_code',                            
        'redirect_uri': 'https://www.googleapis.com/userinfo/v2/me'
        }                 

dgt = OAuth2Service(
           name='clientB',
           client_id="clientA",
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
         'scope'  : ['calendar'] ,                                              
        'redirect_uri': 'http://127.0.0.1:8003/calendar'
        }



#github = OAuth2Session('sparsov', 'Ghbdtnueuk.1964', access_token='Ghbdtnueuk.1964')
test = 'google'
#test = 'gith'
github = OAuth2Service(
    client_id='sparsov',
    client_secret='Ghbdtnueuk.1964',
    name='github',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    base_url='https://api.github.com/'
    )

#print ('Visit this URL in your browser: ',github.get_authorize_url(**params))
#data = dict(code='foobar', redirect_uri='https://api.github.com/user')
#session = github.get_auth_session(data=data)
#print('logged',session)

def main():
    print(f'test: {test}')
    if test == 'git':
        url = gitservice.get_authorize_url(**params)
        print('URL',url)
        request_token, request_token_secret = gitservice.get_access_token()
        session = gitservice.get_session('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')

        #session = service.get_auth_session('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','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')
    elif test == 'google':
        
        #url = googleserv.get_authorize_url(**goog_params)
        #print('URL',url)
        #token = dgt.get_access_token()
        #print('token',token)
        session = dgt.get_auth_session(data=dgt_data)#,decoder=decode_json)
        print('session',session)
        ret = session.request('GET', 'http://127.0.0.1:8003/calendar')
        print('ret',ret,ret.content)
        ret = session.request('GET', 'http://127.0.0.1:8003/mail') 
        if ret.status_code == 200:
            print('ret',ret,ret.content)  
        else:
            print('ret',ret.status_code)




if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    

    
