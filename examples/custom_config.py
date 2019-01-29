"""
Example for a custom config.

At some point, your client will probably need to have it's own config mechanism
for your app-specific config values. To use a custom config, all you need to
do is provide the read/write/clear hooks.
"""
from native_login import NativeClient, TokenStorage
from myconfig import config


class MyTokenStorage(TokenStorage):

    def write(self, tokens):
        config.save(tokens, section='tokens')

    def read(self):
        config.load(section='tokens')

    def clear(self):
        config.remove(section='tokens')


# Using your custom Token Handler:
app = NativeClient(client_id='b61613f8-0da8-4be7-81aa-1c89f2c0fe9f',
                   token_handler=MyTokenStorage())

# Calls write()
app.login()

# Calls read()
tokens = app.load_tokens()

# Calls clear()
app.revoke_tokens()
