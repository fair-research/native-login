.. _sdk_reference_token_storage:

Token Storage
=============

Configure custom token storage for a NativeClient. Custom token storage can be configured
by passing in a complient instance as ``token_storage``, shown below.

.. code-block:: python

    from fair_research_login import NativeClient, JSONTokenStorage

    app = NativeClient(
        client_id='my-client-id',
        token_storage=JSONTokenStorage('mytokens.json')
    )


.. autoclass:: fair_research_login.MultiClientTokenStorage
   :members:
   :member-order: bysource
   :show-inheritance:


.. autoclass:: fair_research_login.ConfigParserTokenStorage
   :show-inheritance:


.. autoclass:: fair_research_login.JSONTokenStorage
   :show-inheritance:
