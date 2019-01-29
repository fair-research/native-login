"""
The most basic usage automatically saves and loads tokens, and provides
a local server for logging in users.
"""
from native_login import NativeClient

# Register an app for a client_id at https://developers.globus.org
tokens = NativeClient(client_id='<client_id>').login()

print(tokens)
