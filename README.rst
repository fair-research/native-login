.. image:: https://travis-ci.org/fair-research/native-login.svg?branch=master
    :target: https://travis-ci.org/fair-research/native-login

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :alt: License
    :target: https://opensource.org/licenses/Apache-2.0

Fair Research Login
===================

This package makes writing Globus scripts and clients a breeze! Easily setup
token management and local server login with a few lines of code. Easily extend
components as your app grows and requires its own config.

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

    from fair_research_login.client import NativeClient

    cli = NativeClient(client_id='<client_id>', app_name='My App')
    cli.login()


The following example uses the Auth API to fetch the logged-in user's identity data and print it:

.. code-block:: python

    from globus_sdk import AuthClient

    auth_client = AuthClient(authorizer=cli.get_authorizers()['auth.globus.org'])
    print(auth_client.oauth2_userinfo())

See the 'examples' directory for extended usage.


Refresh Tokens
--------------

By default, regular tokens will expire in a couple days. You can request refresh tokens to make
user logins last forever. This is handy if you need to do long running tasks or small tasks
every day, but you need to be *absolutely certain these tokens are in a secure location*.

Request refresh tokens with one extra argument to login:

.. code-block:: python

    cli.login(refresh_tokens=True)


Testing
-------

Install the test requirements:

    pip install -r test-requirements.txt

Run pytest:

    pytest

See coverage with a couple more arguments:

    pytest --cov=fair_research_login tests/
