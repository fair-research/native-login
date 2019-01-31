"""
The most basic usage automatically saves and loads tokens, and provides
a local server for logging in users.
"""
from native_login import NativeClient

# Register an app for a client_id at https://developers.globus.org
client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5')

# Automatically saves tokens in ~/.globus-native-apps.cfg
tokens = client.login(requested_scopes=['openid'])

print(tokens)
