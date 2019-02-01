from globus_sdk import NativeAppAuthClient

from native_login.code_handler import InputCodeHandler
from native_login.local_server import LocalServerCodeHandler
from native_login.token_storage import (
    MultiClientTokenStorage, check_expired, check_scopes
)
from native_login.exc import LoadError


class NativeClient(NativeAppAuthClient):

    def __init__(self, token_storage=MultiClientTokenStorage(),
                 local_server_code_handler=LocalServerCodeHandler(),
                 secondary_code_handler=InputCodeHandler(),
                 *args, **kwargs):
        super(NativeClient, self).__init__(*args, **kwargs)
        self.token_storage = token_storage
        self.app_name = kwargs.get('app_name') or 'My App'
        self.local_server_code_handler = local_server_code_handler
        self.local_server_code_handler.set_app_name(self.app_name)
        self.secondary_code_handler = secondary_code_handler
        if isinstance(self.token_storage, MultiClientTokenStorage):
            self.token_storage.set_client_id(kwargs.get('client_id'))

    def login(self, no_local_server=False, no_browser=False,
              requested_scopes=(), refresh_tokens=None,
              prefill_named_grant=None, additional_params=None, force=False):

        if force is False:
            try:
                return self.load_tokens(requested_scopes=requested_scopes)
            except (LoadError, Exception):
                pass

        grant_name = prefill_named_grant or '{} Login'.format(self.app_name)
        code_handler = (self.secondary_code_handler
                        if no_local_server else self.local_server_code_handler)

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
            serialized_tokens = self.token_storage.serialize_tokens(tokens)
            return self.token_storage.write_tokens(serialized_tokens)
        raise LoadError('No token_storage set on client.')

    def _load_raw_tokens(self):
        """
        Loads tokens without checking them
        :return: tokens by resource server, or an exception if that fails
        """
        if self.token_storage is not None:
                serialized_tokens = self.token_storage.read_tokens()
                return self.token_storage.deserialize_tokens(serialized_tokens)
        raise LoadError('No token_storage set on client.')

    def load_tokens(self, requested_scopes=None):
        tokens = self._load_raw_tokens()

        if not tokens:
            raise LoadError('No Tokens loaded')

        check_scopes(tokens, requested_scopes)
        check_expired(tokens)

        return tokens

    def revoke_tokens(self):
        """
        Revoke saved tokens and clear them from storage
        :return: True if saved tokens were revoked, false if tokens could not
        be loaded
        """
        self.revoke_token_set(self._load_raw_tokens())
        self.token_storage.clear_tokens()

    def revoke_token_set(self, tokens):
        for rs, tok_set in tokens.items():
            self.oauth2_revoke_token(tok_set.get('access_token'))
            self.oauth2_revoke_token(tok_set.get('refresh_token'))
