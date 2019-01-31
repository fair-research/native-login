from native_login import NativeClient, LocalServerCodeHandler

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

print(tokens)
