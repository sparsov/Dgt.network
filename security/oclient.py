from aioauth_client import OAuth2Client,GithubClient

github = GithubClient(
    client_id='b6281b6fe88fa4c313e6',
    client_secret='21ff23d9f1cad775daee6a38d230e1ee05b04f7c',
)


class Dgt2Client(OAuth2Client):
    """Support Google.
    * Dashboard: https://console.developers.google.com/project
    * Docs: https://developers.google.com/accounts/docs/OAuth2
    * API reference: https://developers.google.com/gdata/docs/directory
    * API explorer: https://developers.google.com/oauthplayground/
    """

    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    access_token_url = "https://oauth2.googleapis.com/token"
    base_url = "https://www.googleapis.com/userinfo/v2/"
    name = "google"
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




if __name__ == '__main__':

    authorize_url = github.get_authorize_url(scope="user:email")
    print("authorize_url",authorize_url)
    # ...
    # Reload client to authorize_url and get code
    # ...

    #otoken, _ = github.get_access_token(code)
