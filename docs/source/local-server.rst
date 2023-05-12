Custom Local Server
===================

The Local Server is the mechanism by which Fair Research Login will attempt to
simplify the Native App Auth flow. It does this by spinning up a new local server
on the user's machine, and using it to pass the auth code from the last leg of the
auth flow. This way, the user does not have to copy-paste the code manually.

The Local Server can also be used to display a small web page to indicate the status
of the login. This can be changed if the developer wishes to change the styling of
the web page for branding reasons. A simple web page example is below:

.. code-block:: python

  from fair_research_login import NativeClient, LocalServerCodeHandler

  template = """
  <h1>Hello $app_name!</h1>
  <p>
    $login_result. You may close this tab.
  </p>
  <p>
    $error
  </p>
  <p>
    $post_login_message
  </p>
  """

  template_vars = {
      'defaults': {
          'app_name': '',  # Auto-populated if blank, but can be changed
          'post_login_message': '',
          'error': '',  # Present if there is an error in Globus Auth
      },
      'success': {
          'login_result': 'Login Successful',
      },
      'error': {
          'login_result': 'Login Failed',
      }
  }

  app = NativeClient(
      client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
      # Turn off token storage for this example
      token_storage=None,
      # Use our custom local server
      local_server_code_handler=LocalServerCodeHandler(template, template_vars),
      # Automatically populates 'app_name' in template if defined
      app_name='Native Login Examples',
  )

  tokens = app.login(no_local_server=False)