# Native Login

This package makes writing Globus scripts and clients a breeze! Easily setup
token management and local server login with a few lines of code. Easily extend
components as your app grows and requires its own config.

### Installation

The only requirements are the Globus SDK. Nothing else is required.

Install with pip:

    pip install -e git+https://github.com/fair-research/native-login#egg=native-login


### Getting Started

You'll need a Client ID from Globus. Follow [these instructions](http://developers.globus.org)
from the Globus Auth Developer Guide. Be sure to check the
**Native App** box in the registration form. Note the Client ID assigned by Globus. 
You'll need it in your code, as shown in the example below.

Usage looks like this:

    from native_login.client import NativeClient

    tokens = NativeClient(client_id='<client_id>', app_name='My App').login()


After that, it's off to scripting:

    from globus_sdk import AccessTokenAuthorizer, AuthClient

    authorizer = AccessTokenAuthorizer(tokens['auth.globus.org']['access_token'])
    auth_client = AuthClient(authorizer=authorizer)
    print(auth_client.oauth2_userinfo())

See the 'examples' directory for extended usage.

### Testing

Install the test requirements:

    pip install -r test-requirements.txt

Run pytest:

    pytest

See coverage with a couple more arguments:

    pytest --cov=native_login tests/
