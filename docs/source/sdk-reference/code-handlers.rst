.. _sdk_reference_code_handlers:

Code Handlers
=============

Code Handers serve as a mechanism to complete the Globus Native App Auth Flow,
by ensuring that the auth code returned as the final leg of the flow is copied
from the globus webapp and exchanged with Globus Auth for tokens.

Special code handlers like the ``LocalServerCodeHandler`` can copy this code
automatically to streamline the auth flow. ``InputCodeHandler`` is less convenient,
but can be used to manually copy the code in the case where the user is logged into
a remote service.

.. code-block:: python

    from fair_research_login import NativeClient, InputCodeHandler, LocalServerCodeHandler

    app = NativeClient(
        client_id='my-client-id',
        code_handlers=[InputCodeHandler, LocalServerCodeHandler],
    )


.. autoclass:: fair_research_login.InputCodeHandler
   :show-inheritance:

.. autoclass:: fair_research_login.LocalServerCodeHandler
   :show-inheritance:

.. autoclass:: fair_research_login.code_handler.CodeHandler
   :members:
   :member-order: bysource
   :show-inheritance:
