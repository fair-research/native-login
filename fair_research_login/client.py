from globus_sdk import (NativeAppAuthClient, RefreshTokenAuthorizer,
                        AccessTokenAuthorizer)

from fair_research_login.code_handler import InputCodeHandler
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.token_storage import (
    MultiClientTokenStorage, check_expired, check_scopes
)
from fair_research_login.exc import (
    LoadError, TokensExpired, TokenStorageDisabled, NoSavedTokens,
    ScopesMismatch
)
from fair_research_login.refresh import RefreshHelper


class NativeClient(object):
    """
    The Native Client serves as another small layer on top of the Globus SDK
    to automatically handle token storage and provide a customizable
    Local Server. It can be used both by simple scripts to simplify the
    auth flow, or by full command line clients that may extend various pieces
    and tailor them to its own needs.
    """

    TOKEN_STORAGE_ATTRS = {'write_tokens', 'read_tokens', 'clear_tokens'}

    def __init__(self, token_storage=MultiClientTokenStorage(),
                 local_server_code_handler=LocalServerCodeHandler(),
                 secondary_code_handler=InputCodeHandler(),
                 default_scopes=None,
                 *args, **kwargs):
        self.client = NativeAppAuthClient(*args, **kwargs)
        self.token_storage = token_storage
        if token_storage is not None:
            self.verify_token_storage(self.token_storage)
        self.app_name = kwargs.get('app_name') or 'My App'
        self.local_server_code_handler = local_server_code_handler
        self.local_server_code_handler.set_app_name(self.app_name)
        self.secondary_code_handler = secondary_code_handler
        if isinstance(self.token_storage, MultiClientTokenStorage):
            self.token_storage.set_client_id(kwargs.get('client_id'))
        self.default_scopes = default_scopes

    def login(self, no_local_server=False, no_browser=False,
              requested_scopes=(), refresh_tokens=None,
              prefill_named_grant=None, additional_params=None, force=False):
        """
        Do a Native App Auth Flow to get tokens for requested scopes. This
        first attempts to load tokens and will simply return those if they are
        valid, and will automatically attempt to save tokens on login success
        (token_storage must be set for automatic load/save functionality).
        :param no_local_server: Don't use the local server. This may be because
        of permissions issues of standing up a server on the clients machine.
        :param no_browser: Don't automatically open a browser, and instead
        instruct the user to manually follow the URL to login. This is useful
        on remote servers which don't have native browsers for clients to use.
        :param requested_scopes: Globus Scopes to request on the users behalf.
        :param refresh_tokens: Use refresh tokens to extend login time
        :param prefill_named_grant: Named Grant to use on Consent Page
        :param additional_params: Additional Params to supply, such as for
        using Globus Sessions
        :param force: Force a login flow, even if loaded tokens are valid.
        :return:
        """
        if force is False:
            try:
                return self.load_tokens(requested_scopes=requested_scopes)
            except (LoadError, Exception):
                pass

        grant_name = prefill_named_grant or '{} Login'.format(self.app_name)
        code_handler = (self.secondary_code_handler
                        if no_local_server else self.local_server_code_handler)

        with code_handler.start():
            self.client.oauth2_start_flow(
                requested_scopes=requested_scopes or self.default_scopes,
                refresh_tokens=refresh_tokens,
                prefill_named_grant=grant_name,
                redirect_uri=code_handler.get_redirect_uri()
            )
            auth_url = self.client.oauth2_get_authorize_url(
                additional_params=additional_params
            )
            auth_code = code_handler.authenticate(url=auth_url,
                                                  no_browser=no_browser)
        token_response = self.client.oauth2_exchange_code_for_tokens(auth_code)
        try:
            tokens = []
            try:
                tokens = self._load_raw_tokens()
            except LoadError:
                pass
            tokens.append(token_response.by_resource_server)
            self.save_tokens(tokens)
        except LoadError:
            pass
        return token_response.by_resource_server

    def verify_token_storage(self, obj):
        for attr in self.TOKEN_STORAGE_ATTRS:
            if getattr(obj, attr, None) is None:
                raise AttributeError('token_storage requires object "{}" to '
                                     'have the {} attribute'.format(obj, attr))

    def save_tokens(self, tokens):
        """
        Save tokens if token_storage is set. Typically this is called
        automatically in a successful login().
        :param tokens: globus_sdk.auth.token_response.OAuthTokenResponse.
        :return: None
        """
        if self.token_storage is not None:
            return self.token_storage.write_tokens(tokens)
        raise TokenStorageDisabled('No token_storage set on client.')

    def _get_newest_token(self, token_group):
        exps = [item['expires_at_seconds'] for item in token_group.values()]
        return max(exps)

    def _load_raw_tokens(self):
        """
        Loads tokens without checking them
        :return: tokens by resource server, or an exception if that fails
        """
        if self.token_storage is not None:
            login_group = self.token_storage.read_tokens()
            login_group.sort(
                key=lambda tgroup: self._get_newest_token(tgroup),
                reverse=True
            )
            return login_group
        raise TokenStorageDisabled('No token_storage set on client.')

    def load_tokens(self, requested_scopes=None):
        """
        Load tokens from the set token_storage object if one exists.
        :param requested_scopes: Check that the loaded scopes match these
        requested scopes. Raises ScopesMismatch if there is a discrepancy.
        :return: Loaded tokens, or a LoadError if loading fails.
        """
        login_list = self._load_raw_tokens()

        if not login_list:
            raise NoSavedTokens('No tokens are available.')

        # Flag to check if there was a scope match when checking tokens. If
        # there was, but they expired, we prefer to throw an expired exception.
        scope_match = False
        for tok_candidate in login_list:
            if requested_scopes not in [None, ()]:
                if not check_scopes(tok_candidate, requested_scopes):
                    continue
            scope_match = True
            try:
                check_expired(tok_candidate)
            except TokensExpired as te:
                expired = {rs: tok_candidate[rs] for rs in te.resource_servers}
                if not self.are_refreshable(expired):
                    continue
                tok_candidate.update(self.refresh_tokens(expired))
                self.save_tokens(login_list)
            return tok_candidate

        if scope_match:
            raise TokensExpired('A previous login matched {} but the tokens '
                                'have expired.'.format(requested_scopes))
        else:
            raise ScopesMismatch('No saved tokens match the scopes: {}'
                                 .format(requested_scopes))

    def refresh_tokens(self, tokens):
        if not self.are_refreshable(tokens):
            raise TokensExpired('No Refresh Token, cannot refresh tokens: ',
                                resource_servers=tokens.keys())

        for rs, token_dict in tokens.items():
            authorizer = RefreshTokenAuthorizer(
                token_dict['refresh_token'],
                self.client,
                access_token=token_dict['access_token'],
                expires_at=token_dict['expires_at_seconds'],
            )
            authorizer.check_expiration_time()
            token_dict['access_token'] = authorizer.access_token
            token_dict['expires_at_seconds'] = authorizer.expires_at
        return tokens

    def get_authorizers(self, requested_scopes=None):
        authorizers = {}
        tokens = self.load_tokens(requested_scopes)
        explicit_scopes = requested_scopes or self.get_scope_set(tokens)
        for resource_server, token_dict in tokens.items():
            if token_dict.get('refresh_token') is not None:
                authorizers[resource_server] = RefreshTokenAuthorizer(
                    token_dict['refresh_token'],
                    self.client,
                    access_token=token_dict['access_token'],
                    expires_at=token_dict['expires_at_seconds'],
                    on_refresh=RefreshHelper(self, explicit_scopes),
                )
            else:
                authorizers[resource_server] = AccessTokenAuthorizer(
                    token_dict['access_token']
                )
        return authorizers

    def logout(self):
        """
        Revoke saved tokens and clear them from storage
        """
        for tset in self._load_raw_tokens():
            self.revoke_token_set(tset)
        self.token_storage.clear_tokens()

    def revoke_token_set(self, tokens):
        for rs, tok_set in tokens.items():
            self.client.oauth2_revoke_token(tok_set.get('access_token'))
            self.client.oauth2_revoke_token(tok_set.get('refresh_token'))

    @staticmethod
    def get_scope_set(token_group):
        scopes = [tset['scope'].split() for tset in token_group.values()]
        flat_list = [item for sublist in scopes for item in sublist]
        return flat_list

    @classmethod
    def check_scopes(cls, tokens, requested_scopes):
        return set(cls.get_scope_set(tokens)) == set(requested_scopes)

    @staticmethod
    def are_refreshable(tokens):
        return all([bool(ts['refresh_token']) for ts in tokens.values()])
