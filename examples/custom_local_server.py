from native_login.client import NativeClient
from native_login.local_server import LocalServerCodeHandler

client_id = 'b61613f8-0da8-4be7-81aa-1c89f2c0fe9f'

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

code_handler = LocalServerCodeHandler(template, template_vars)

app = NativeClient(
    client_id=client_id,
    local_server_code_handler=code_handler,
    # Automatically populates 'app_name' in template if defined
    app_name='My Brand New App',
    )
app.login(no_local_server=False)
