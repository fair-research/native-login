"""
Typically, you want to save tokens after login. The simplest solution is
to use the built in helpers. This is best for scripting. If you're writing
a custom client and want more control over your config, see the complex config
module.
"""
from fair_research_login import NativeClient

# Supported built-in storage mechanisms
from fair_research_login import JSONTokenStorage  # noqa

app = NativeClient(
    # Registered client on http://developers.globus.org
    client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
    token_storage=JSONTokenStorage('mytokens.json')
)

# Saves tokens
app.login()

# Loads tokens
app.load_tokens()

# Clears tokens
app.logout()
