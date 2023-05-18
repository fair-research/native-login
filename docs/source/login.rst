Configuring Login
=================

Fair Research Login behavior can be customized by passing in a few basic arguments.
Common changes are below:

.. code-block:: python

    from globus_sdk import AuthClient
    from fair_research_login import NativeClient

    # Register a Native App for a client_id at https://developers.globus.org
    client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')


    # Automatically saves tokens in ~/.globus-native-apps.cfg
    tokens = client.login(
        # Request any scopes you want to use here.
        requested_scopes=['openid', 'profile'],
        # You can turn off the local server if it cannot be used for some reason
        no_local_server=False,  #  (default=True)
        # You can also turn off automatically opening the Auth URL in the user's browser
        no_browser=False,  # (default=True)
        # request refresh tokens to extend login
        refresh_tokens=True,  # (default=False)
    )


The code above will run once and prompt the user for login. A _second_ run of the
code will do nothing, loading tokens from disk instead of prompting the user for
an auth code.

Other common arguments above change the behavior of the login flow, including which
scopes it requests, if it will attempt to automatically copy the auth-code, open the
user's browser, or request refresh tokens. See more in the reference documentation.


Additional common operations for token handling is below:


.. code-block:: python

    # Calling login() twice will load tokens instead of initiating an oauth flow,
    # as long as the requested scopes match and the tokens have not expired.
    assert tokens == client.login(requested_scopes=['openid', 'profile'])

    # You can also load tokens explicitly. This will also load tokens if you have
    # done other logins
    assert tokens == client.load_tokens()
    # If you want to disregard other saved tokens
    assert tokens == client.load_tokens(requested_scopes=['openid', 'profile'])

    # Loading by scope is also supported
    tokens_by_scope = client.load_tokens_by_scope()
    assert set(tokens_by_scope.keys()) == {'openid', 'profile'}

    # Authorizers automatically choose a refresh token authorizer if possible,
    # and will automatically save new refreshed tokens when they expire.
    ac_authorizer = client.get_authorizers()['auth.globus.org']
    # Also supported
    ac_authorizer = client.get_authorizers_by_scope()['openid']

    # Example client usage:
    auth_cli = AuthClient(authorizer=ac_authorizer)
    user_info = auth_cli.oauth2_userinfo()
    print('Hello {}! How are you today?'.format(user_info['name']))

    # Revoke tokens now that we're done
    client.logout()

Error Handling
--------------

Apps should incorperate some error handling in the case where Fair Research Login
can't recover from a given error. Some cases involve the user declining consent to
use an app, or attempting to load tokens which have expired.

.. code-block:: python

    import sys
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
