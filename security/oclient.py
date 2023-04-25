from aioauth_client import OAuth2Client,GithubClient
import asyncio
github = GithubClient(
    client_id='40262793', #sparsov',
    client_secret="Ghbdtnueuk.1964" #'Ghbdtnueuk.1964', #"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"
)
github1 = GithubClient(
    client_id='sparsov',
    client_secret='Ghbdtnueuk.1964',
    access_token="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",
)

class Dgt2Client(OAuth2Client):
    """Support DGT.
    * Dashboard: https://console.developers.google.com/project
    * Docs: https://developers.google.com/accounts/docs/OAuth2
    * API reference: https://developers.google.com/gdata/docs/directory
    * API explorer: https://developers.google.com/oauthplayground/
    """

    authorize_url = "http://127.0.0.1:8003/authorize" #"https://accounts.google.com/o/oauth2/v2/auth"
    access_token_url = "http://127.0.0.1:8003/token" #"https://oauth2.googleapis.com/token"
    base_url = "https://www.googleapis.com/userinfo/v2/"
    name = "dgt"
    user_info_url = "https://www.googleapis.com/userinfo/v2/me"

    @staticmethod
    def user_parse(data):
        """Parse information from provider."""
        yield "id", data.get("id")
        yield "email", data.get("email")
        yield "first_name", data.get("given_name")
        yield "last_name", data.get("family_name")
        yield "link", data.get("link")
        yield "locale", data.get("locale")
        yield "picture", data.get("picture")
        yield "gender", data.get("gender")


dgt = Dgt2Client(client_id='sparsov',                          
                 client_secret='Ghbdtnueuk.1964',  
                 )

def main():
    async def test():
        authorize_url = github.get_authorize_url(scope="user:email")               
        print("authorize_url",authorize_url,dir(github))

        token,_ = await github1.get_access_token("json") #authorize_url)                    
        #token,_ = github.get_request_token()                                      
        #print("token",token) 
        response = await github1.request('GET', 'user')      
        #user_info = await response.json()                  
        print("user_info",response)                         
                                                       
        
    async def test1():                                                         
        authorize_url = dgt.get_authorize_url(scope="user:email")             
        print("DGT::authorize_url",authorize_url)                             
        token,_ = await  dgt.get_access_token("json")                  
        print("token",token)







    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(test())]                                
    wait_tasks = asyncio.wait(tasks)
    loop.run_until_complete(wait_tasks)
    loop.close()








if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    
    
    
    

    
