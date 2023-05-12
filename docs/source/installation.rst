Installation and Basic Usage
============================

Install with pip:

.. code-block:: bash
  
  pip install fair-research-login


Getting Started
---------------

You'll need a Client ID from Globus. Follow these instructions from the `Globus Auth Developer Guide <https://docs.globus.org/api/auth/developer-guide/#register-app>`_.
Be sure to check the **Native App** box in the registration form. Note the Client ID assigned by Globus.
You'll need it in your code, as shown in the example below.

Usage looks like this:

.. code-block:: python

    from globus_sdk import AuthClient
    from fair_research_login.client import NativeClient

    # Login. Replace your client_id below with the one generated from https://developers.globus.org
    cli = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5', app_name='My App')
    cli.login(requested_scopes=['openid', 'email', 'profile'], refresh_tokens=True)

    # Use your tokens
    auth_client = AuthClient(authorizer=cli.get_authorizers()['auth.globus.org'])
    print(auth_client.oauth2_userinfo())
