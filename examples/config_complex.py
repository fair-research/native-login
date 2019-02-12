"""
Example for a custom config.

At some point, your client will probably need to have it's own config mechanism
for your app-specific config values. To use a custom config, all you need to
do is provide the read_tokens/write_tokens/clear_tokens functions in an object.
"""
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
            json.dump(tokens.by_resource_server, fh, indent=2)

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
        with open(self.FILENAME) as fh:
            return json.load(fh)

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

# Calls read_tokens() then write_tokens()
app.login()

# Calls read_tokens()
app.load_tokens()

# Calls clear_tokens()
app.logout()
