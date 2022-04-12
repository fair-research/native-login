"""
Here are some edge cases you may have to deal with in more complex scripts.
"""
import sys
import globus_sdk
from fair_research_login import NativeClient, TokensExpired
from fair_research_login.exc import LocalServerError, AuthFailure

# Register a Native App for a client_id at https://developers.globus.org
client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')

"""
Handling when the user does not consent
"""

try:
    client.login(
        requested_scopes=['openid', 'profile'],
        # Using the local server will essentially copy the auth code returned
        # by Globus to a local webserver, where it can automatically be handed
        # to the globus_sdk. The most likely error is Globus responds with an
        # error instead of a code.
        #
        # Alternatively, with no local server, we simply wait for a code. The
        # more likely case there is the user enters garbage which results in an
        # invalid grant.
        no_local_server=True,
        )
    print('Login Successful')
except LocalServerError as lse:
    # There was some problem with the local server, likely the user clicked
    # "Decline" on the consents page
    print(f'Login Unsuccessful: {str(lse)}')
    sys.exit(1)
except AuthFailure as auth_failure:
    # Something went wrong with getting the auth code
    print(f'Login Unsuccessful: {str(auth_failure)}')
    sys.exit(2)

"""
Token Expiration
"""

# Let's start off by manually expiring some tokens
client.save_tokens(
    {'auth.globus.org': {
        'scope': 'openid profile',
        'access_token': '<fake_access_token>',
        'expires_at_seconds': 0,
        'resource_server': 'auth.globus.org',
        }
     }
)
try:
    client.load_tokens(requested_scopes=['openid', 'profile'])
except TokensExpired as te:
    print('Load Failure, tokens expired for: {}'.format(te))
