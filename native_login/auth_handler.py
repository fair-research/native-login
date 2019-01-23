from globus_sdk import NativeAppAuthClient

from native_login.code_handler import InputCodeHandler, LocalServerHandler


class NativeAppHandler:

    def __init__(self, client_id=None, app_name='Anonymous App',
                 requested_scopes=(), refresh_tokens=False,
                 prefill_named_grant='', additional_params={},
                 save_tokens_callback=None):
        self.app_name = app_name
        self.client_id = client_id
        self.requested_scopes = requested_scopes
        self.refresh_tokens = refresh_tokens
        self.prefill_named_grant = (prefill_named_grant or
                                    'Login for {}'.format(app_name))
        self.additional_params = additional_params
        self.client = self.get_client()
        if save_tokens_callback is None or not callable(save_tokens_callback):
            self.save_tokens_callback = save_tokens_callback
        else:
            raise ValueError('Expected a function for "save_tokens_callback", '
                             'got {} instead.'.format(save_tokens_callback))

    def get_client(self):
        return NativeAppAuthClient(app_name=self.app_name,
                                   client_id=self.client_id)

    def get_authorize_url(self, redirect_uri):
        self.client.oauth2_start_flow(
            requested_scopes=self.requested_scopes,
            redirect_uri=redirect_uri,
            refresh_tokens=self.refresh_tokens,
            prefill_named_grant=self.prefill_named_grant
        )
        url = self.client.oauth2_get_authorize_url(
            additional_params=self.additional_params
        )
        return url

    def login(self, no_local_server=False, no_browser=False):
        code_handler = (InputCodeHandler() if no_local_server
                        else LocalServerHandler())
        auth_url = self.get_authorize_url(code_handler.redirect_uri)
        auth_code = code_handler.authenticate(url=auth_url,
                                              no_browser=no_browser)
        token_response = self.client.oauth2_exchange_code_for_tokens(auth_code)
        tokens_by_resource_server = token_response.by_resource_server
        if self.save_tokens_callback:
            self.save_tokens_callback(tokens_by_resource_server)
        return token_response

    def revoke_tokens(self, tokens):
        return len([self.client.oauth2_revoke_token(t) for t in tokens])

