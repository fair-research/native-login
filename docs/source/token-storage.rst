Token Storage
=============

Fair Research Login automatically saves and loads tokens as needed to
reduce the number of logins. This behavior can be further customized
to suit an apps needs.

Simple Storage
--------------

Existing token storage objects exist and can be used if the customization
needs are simple. JSONTokenStorage below can be used to store the tokens as
JSON in a location of the user's choice, in the example below the local
location 'mytokens.json':


.. code-block:: python

    from fair_research_login import NativeClient

    # Supported built-in storage mechanisms
    from fair_research_login import JSONTokenStorage  # noqa

    app = NativeClient(
        # Registered client on http://developers.globus.org
        client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
        token_storage=JSONTokenStorage('mytokens.json')
    )

Advanced Storage
----------------

Further customizing the login behavior can be done by writing a new object that
follows the protocol for storage. A custom storage object must have three methods
that match the signatures below for write_tokens, read_tokens, and clear_tokens.

.. code-block:: python

    import json
    import os
    from fair_research_login import NativeClient


    class MyTokenStorage(object):
        FILENAME = 'my_tokens.json'

        def write_tokens(self, tokens):
            """
            Write tokens to disk. 'tokens' above will be in this format:
            {
                'auth.globus.org': {
                    'scope': 'openid profile email',
                    'access_token': '<token>',
                    'refresh_token': None,
                    'token_type': 'Bearer',
                    'expires_at_seconds': DEFAULT_EXPIRE,
                    'resource_server': 'auth.globus.org'
                },
                <More Token Dicts>
            }
            Some configs, like ConfigParser on python 2.7, do not allow nested
            sections. In that case you can use these tools:

            from native_client.token_storage import flat_pack, flat_unpack
            """
            with open(self.FILENAME, 'w+') as fh:
                json.dump(tokens, fh, indent=2)

        def read_tokens(self):
            """
            Read and return tokens from disk. Returned tokens MUST be of the
            format below:
            {
                'auth.globus.org': {
                    'scope': 'openid profile email',
                    'access_token': '<token>',
                    'refresh_token': None,
                    'token_type': 'Bearer',
                    'expires_at_seconds': DEFAULT_EXPIRE,
                    'resource_server': 'auth.globus.org'
                },
                <More Token Dicts>
            }
            Note: This is the same format returned by the property:
            globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server

            No need to check expiration, that's handled by NativeClient.
            """
            try:
                with open(self.FILENAME) as fh:
                    return json.load(fh)
            except Exception:
                return {}

        def clear_tokens(self):
            """
            Delete tokens from where they are stored. Before this method is called,
            tokens will have been revoked. This is both for cleanup and to ensure
            inactive tokens are not accidentally loaded in the future.
            """
            os.remove(self.FILENAME)


    # Provide an instance of your config object to Native Client. The only
    # restrictions are your client MUST have the three methods above,
    # or it will throw an AttributeError.
    app = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
                    token_storage=MyTokenStorage())