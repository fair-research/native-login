.. image:: https://github.com/fair-research/native-login/actions/workflows/tests.yml/badge.svg
    :target: https://github.com/fair-research/native-login/actions/workflows/

.. image:: https://img.shields.io/pypi/v/fair-research-login.svg
    :target: https://pypi.python.org/pypi/fair-research-login

.. image:: https://img.shields.io/pypi/wheel/fair-research-login.svg
    :target: https://pypi.python.org/pypi/fair-research-login

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/Apache-2.0

Fair Research Login
===================

Fair Research Login simplifies the Globus Auth Flow to facilitate application
development by providing automatic token management and streamlining the native
app grant process. This is useful for writing re-usable scripts and can be used
as the foundation for new applications without investing significant resources in
authentication code.

Installation
------------

The only requirements are the Globus SDK. Nothing else is required.

Install with pip:

.. code-block:: python

    pip install fair-research-login


Getting Started
---------------

You'll need a Client ID from Globus. Follow `these instructions <https://docs.globus.org/api/auth/developer-guide/#register-app>`_
from the Globus Auth Developer Guide. Be sure to check the
**Native App** box in the registration form. Note the Client ID assigned by Globus. 
You'll need it in your code, as shown in the example below.

Usage looks like this:

.. code-block:: python

    from globus_sdk import AuthClient
    from fair_research_login.client import NativeClient

    # Login
    cli = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5', app_name='My App')
    cli.login(requested_scopes=['openid', 'email', 'profile'], refresh_tokens=True)

    # Use your tokens
    auth_client = AuthClient(authorizer=cli.get_authorizers()['auth.globus.org'])
    print(auth_client.oauth2_userinfo())


Support
-------

For any questions or issues using Fair Research Login, please send an email to support@globus.org
with "Fair Research Login" in the message header.