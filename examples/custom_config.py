"""
Example for a custom config.

At some point, your client will probably need to have it's own config mechanism
for your app-specific config values. To use a custom config, all you need to
do is provide the read_tokens/write_tokens/clear_tokens functions in an object.
"""
import json
import os
from native_login import NativeClient


class MyTokenStorage(object):
    FILENAME = 'my_tokens.json'

    def write_tokens(self, tokens):
        with open(self.FILENAME, 'w+') as fh:
            json.dump(tokens.by_resource_server, fh, indent=2)

    def read_tokens(self):
        with open(self.FILENAME) as fh:
            return json.load(fh)

    def clear_tokens(self):
        os.remove(self.FILENAME)


# Using your custom Token Handler:
app = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
                   token_storage=MyTokenStorage())

# Calls read_tokens() then write_tokens()
app.login()

# Calls read_tokens()
app.load_tokens()

# Calls clear_tokens()
app.revoke_tokens()
