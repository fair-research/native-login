from globus_sdk import NativeAppAuthClient

from native_login.code_handler import InputCodeHandler, LocalServerCodeHandler


class NativeClient(NativeAppAuthClient):

    def __init__(self, token_handler=None, local_server_code_handler=None,
                 requested_scopes=None, *args, **kwargs):
        super(NativeClient, self).__init__(*args, **kwargs)
        self.token_handler = token_handler
        self.code_handler = local_server_code_handler
        self.requested_scopes = requested_scopes
        self.app_name = kwargs.get('app_name')

    def login(self, no_local_server=False, no_browser=False,
              requested_scopes=(), refresh_tokens=None,
              prefill_named_grant=None, additional_params=None):
        code_handler = (InputCodeHandler() if no_local_server
                        else LocalServerCodeHandler())
        name = self.app_name or 'Anonymous Client'
        grant_name = prefill_named_grant or 'Grant for {}'.format(name)

        self.oauth2_start_flow(refresh_tokens=refresh_tokens,
                               prefill_named_grant=grant_name,
                               redirect_uri=code_handler.redirect_uri)
        auth_url = self.oauth2_get_authorize_url(
            additional_params=additional_params
        )
        try:
            auth_code = self.code_handler.authenticate(url=auth_url,
                                                       no_browser=no_browser)
        except Exception:
            auth_code = InputCodeHandler().authenticate(url=auth_url,
                                                        no_browser=no_browser)
        token_response = self.oauth2_exchange_code_for_tokens(auth_code)
        self.save_tokens(token_response)
        return token_response

    def save_tokens(self, tokens):
        if self.token_handler is not None:
            serialized_tokens = self.token_handler.serialize(tokens)
            return self.token_handler.write(serialized_tokens)

    def load_tokens(self):
        if self.token_handler is not None:
            serialized_tokens = self.token_handler.read()
            return self.token_handler.deserialize(serialized_tokens)

    def revoke_tokens(self):
        tokens = self.load_tokens()
        for rs, tok_set in tokens.items():
            self.oauth2_revoke_token(tok_set.get('access_token'))
            self.oauth2_revoke_token(tok_set.get('refresh_token'))
        else:
            return False
        return True
