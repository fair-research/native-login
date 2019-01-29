import time
from globus_sdk import NativeAppAuthClient

from native_login.code_handler import InputCodeHandler
from native_login.local_server import LocalServerCodeHandler
from native_login.token_storage import MultiClientTokenStorage
from native_login.exc import LoadError, TokensExpired, ScopesMismatch


class NativeClient(NativeAppAuthClient):

    def __init__(self, token_storage=MultiClientTokenStorage(),
                 local_server_code_handler=None, *args, **kwargs):
        super(NativeClient, self).__init__(*args, **kwargs)
        self.token_storage = token_storage
        self.app_name = kwargs.get('app_name') or 'My App'
        self.local_server = (local_server_code_handler or
                             LocalServerCodeHandler())
        self.local_server.set_app_name(self.app_name)
        if isinstance(self.token_storage, MultiClientTokenStorage):
            self.token_storage.set_client_id(kwargs.get('client_id'))

    def login(self, no_local_server=False, no_browser=False,
              requested_scopes=(), refresh_tokens=None,
              prefill_named_grant=None, additional_params=None, force=False):

        if force is False:
            try:
                return self.load_tokens(requested_scopes=requested_scopes)
            except LoadError:
                pass

        grant_name = prefill_named_grant or '{} Login'.format(self.app_name)
        code_handler = (InputCodeHandler()
                        if no_local_server else self.local_server)

        with code_handler.start():
            self.oauth2_start_flow(
                requested_scopes=requested_scopes,
                refresh_tokens=refresh_tokens,
                prefill_named_grant=grant_name,
                redirect_uri=code_handler.get_redirect_uri()
            )
            auth_url = self.oauth2_get_authorize_url(
                additional_params=additional_params
            )
            auth_code = code_handler.authenticate(url=auth_url,
                                                  no_browser=no_browser)
        token_response = self.oauth2_exchange_code_for_tokens(auth_code)
        self.save_tokens(token_response)
        return token_response.by_resource_server

    def save_tokens(self, tokens):
        if self.token_storage is not None:
            serialized_tokens = self.token_storage.serialize(tokens)
            return self.token_storage.write(serialized_tokens)

    def load_tokens(self, requested_scopes=None):
        if self.token_storage is not None:
            serialized_tokens = self.token_storage.read()
            tokens = self.token_storage.deserialize(serialized_tokens)

            if not tokens:
                raise LoadError('No Tokens loaded')

            if requested_scopes not in [(), None]:
                scopes = [tset['scope'].split() for tset in tokens.values()]
                flat_list = [item for sublist in scopes for item in sublist]
                if set(flat_list) != set(requested_scopes):
                    raise ScopesMismatch('Requested Scopes do not match loaded'
                                         ' Scopes for Globus Auth.')

            expired = [
                time.time() >= t["expires_at_seconds"]
                for t in tokens.values()
            ]
            if any(expired):
                raise TokensExpired()

            return tokens
        raise LoadError('No token_storage set on app. (Try JSONTokenStorage)')

    def revoke_tokens(self):
        try:
            tokens = self.load_tokens()
            for rs, tok_set in tokens.items():
                self.oauth2_revoke_token(tok_set.get('access_token'))
                self.oauth2_revoke_token(tok_set.get('refresh_token'))
            self.token_storage.clear()
            return True
        except LoadError:
            pass
        return False
