"""
The most basic usage automatically saves and loads tokens, and provides
a local server for logging in users.
"""
from globus_sdk import AuthClient
from fair_research_login import NativeClient

# Register a Native App for a client_id at https://developers.globus.org
client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')

# Automatically saves tokens in ~/.globus-native-apps.cfg
tokens = client.login(
    # Request any scopes you want to use here.
    requested_scopes=['openid', 'profile'],
    # You can turn off the local server if it cannot be used for some reason
    no_local_server=False,
    # You can also turn off automatically opening the Auth URL
    no_browser=False,
    # refresh tokens are fully supported, but optional
    refresh_tokens=True,
)

# Authorizers automatically choose a refresh token authorizer if possible,
# and will automatically save new refreshed tokens when they expire.
ac_authorizer = client.get_authorizers()['auth.globus.org']

# Example client usage:
auth_cli = AuthClient(authorizer=ac_authorizer)
user_info = auth_cli.oauth2_userinfo()
print('Hello {}! How are you today?'.format(user_info['name']))

# Revoke tokens now that we're done
client.logout()
