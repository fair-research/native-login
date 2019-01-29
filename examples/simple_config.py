"""
Typically, you want to save tokens after login. The simplest solution is
to use the built in helpers. This is best for scripting. If you're writing
a custom client and want more control over your config, see the 'custom config'
module.
"""

from native_login.client import NativeClient
from native_login.token_handlers.json_token_handler import JSONTokenHandler

app = NativeClient(client_id='b61613f8-0da8-4be7-81aa-1c89f2c0fe9f',
                   token_handler=JSONTokenHandler())

# saves tokens at ~/.globus-native-apps.cfg
app.login()

# loads tokens saved to file
tokens = app.load_tokens()
