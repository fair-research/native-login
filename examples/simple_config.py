"""
Typically, you want to save tokens after login. The simplest solution is
to use the built in helpers. This is best for scripting. If you're writing
a custom client and want more control over your config, see the 'custom config'
module.
"""

from native_login import NativeClient, JSONTokenStorage, LoadError

# Registered client on http://developers.globus.org
CLIENT_ID = '<CLIENT_ID>'

app = NativeClient(client_id=CLIENT_ID, token_handler=JSONTokenStorage())

try:
    # Loads tokens instead of doing a login flow
    tokens = app.load_tokens()
except LoadError:
    # saves tokens at ~/.globus-native-apps.cfg
    tokens = app.login()

# Show tokens
print(tokens)

# Revoke tokens and clear them from the config file when finished
app.revoke_tokens()
