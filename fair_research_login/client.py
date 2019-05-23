import time
from globus_sdk import (NativeAppAuthClient, RefreshTokenAuthorizer,
                        AccessTokenAuthorizer)

from fair_research_login.code_handler import InputCodeHandler
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.token_storage import MultiClientTokenStorage
from fair_research_login.exc import (
    LoadError, TokensExpired, TokenStorageDisabled, NoSavedTokens,
    ScopesMismatch
)
from fair_research_login.refresh import RefreshHelper


class NativeClient(object):
    r"""
    The Native Client serves as another small layer on top of the Globus SDK
    to automatically handle token storage and provide a customizable
    Local Server. It can be used both by simple scripts to simplify the
    auth flow, or by full command line clients that may extend various pieces
    and tailor them to its own needs.
    **Parameters**
        ``client_id`` (*string*)
          The id for your app. Register one at https://developers.globus.org
        ``app_name`` (*string*)
          The name of your app. Shows up on the named grant during consent,
          and the local server browser page by default. It is also propogated
          to globus_sdk.NativeAppAuthClient.
        ``default_scopes`` (*list*)
          A list of scopes which will serve as the default to login() if
          login is called with no requested_scopes parameter.
          Example:
          ['openid', 'profile', 'email']
        ``token_storage`` (*object*)
          Any object capable of reading/writing/clearing tokens from/to disk.
          The object must define these three methods: read_tokens(),
          write_tokens(tokens), and clear_tokens(), where ``tokens`` is a list
          of login groups (dicts), each of which contains a token group (dict)
          keyed by resource server.

          Example ``tokens``:
          [{
            'auth.globus.org': {
                'scope': 'openid profile email',
                'access_token': '<token>',
                'refresh_token': None,
                'token_type': 'Bearer',
                'expires_at_seconds': 1234567,
                'resource_server': 'auth.globus.org'
            }
          }]

          A default token storage object is provided
          at fair_research_login.token_storage.MultiClientTokenStorage, which
          saves tokens in a section named by your clients ``client_id``. None
          may be used to disable token storage.
        ``local_server_code_handler`` (:class:`CodeHandler \
          <fair_research_login.code_handler.CodeHandler>`)
          A Local Code handler capable of fetching and returning the
          authorization code generated as a browser query param in Globus Auth
          Used during login(), but can be disabled with
          login(no_local_server=True)
        ``secondary_code_handler`` (:class:`CodeHandler \
          <fair_research_login.code_handler.CodeHandler>`)
          Handler to be used if the ``local_server_code_handler`` has been
          disabled.

    ** Methods **

    *  :py:meth:`.login`
    *  :py:meth:`.logout`
    *  :py:meth:`.load_tokens`
    *  :py:meth:`.get_authorizers`
    *  :py:meth:`.revoke_token_set`
    *  :py:meth:`.are_refreshable`
    *  :py:meth:`.check_scopes`
    *  :py:meth:`.get_scope_set`
    *  :py:meth:`.refresh_tokens`

    ** Example **

    cli = NativeClient(client_id='my_id', app_name='my cool app')
    cli.login(requested_scopes=['openid', 'profile', 'email'])
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
        See ``load_tokens`` for how it handles requested_scopes.
        **Parameters**
        ``no_local_server`` (*bool*)
          Disable spinning up a local server to automatically copy-paste the
          auth code. THIS IS REQUIRED if you are on a remote server, as this
          package isn't able to determine the domain of a remote service. When
          used locally with no_local_server=False, the domain is localhost with
          a randomly chosen open port number.
        ``no_browser`` (*string*)
          Do not automatically open the browser for the Globus Auth URL.
          Display the URL instead and let the user navigate to that location.
        ``requested_scopes`` (*list*)
          A list of scopes to request of Globus Auth during login.
          Example:
          ['openid', 'profile', 'email']
        ``refresh_tokens`` (*bool*)
          Ask for Globus Refresh Tokens to extend login time.
        ``prefill_named_grant`` (*bool*)
          Use a custom named grant on the consent page
        ``additional_params`` (*dict*)
          Additional Params used in constructing the authorize URL for Globus
          Auth. Used for requesting additional features such as for using
          Globus Sessions.
        ``force`` (*bool*)
          Force a login flow, even if loaded tokens are valid.
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
        """
        Internal. Verify object passed for token_storage is valid.
        """
        for attr in self.TOKEN_STORAGE_ATTRS:
            if getattr(obj, attr, None) is None:
                raise AttributeError('token_storage requires object "{}" to '
                                     'have the {} attribute'.format(obj, attr))

    def save_tokens(self, tokens):
        r"""
        Save tokens if token_storage is set. Typically this is called
        automatically in a successful login().
        **Parameters**
        ``tokens`` (**list**)
          A list of all user logins, each containing a dict defined by
            globus_sdk.auth.token_response.OAuthTokenResponse\
            .by_resource_server.
        """
        if self.token_storage is not None:
            return self.token_storage.write_tokens(tokens)
        raise TokenStorageDisabled('No token_storage set on client.')

    def _get_newest_token(self, token_group):
        exps = [item['expires_at_seconds'] for item in token_group.values()]
        return max(exps)

    def _load_raw_tokens(self):
        """
        Loads tokens without checking whether they have expired. Sorts them by
        expiration time.
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
        Load tokens from the set token_storage object if one exists. If
        requested_scopes is None, it returns the most recent login tokens.
        Otherwise, it searches for unexpired tokens which match the
        requested scopes. Raises ScopesMismatch if no scopes match, and
        TokensExpired if there was a match but they expired.
        **Parameters**
        ``requested_scopes`` (*list*)
          A list of scopes. Example:
          ['openid', 'profile', 'email']
        """
        if requested_scopes is not None and isinstance(requested_scopes, str):
            requested_scopes = requested_scopes.split(' ')

        login_list = self._load_raw_tokens()

        if not login_list:
            raise NoSavedTokens('No tokens are available.')

        # Flag to check if there was a scope match when checking tokens. If
        # there was, but they expired, we prefer to throw an expired exception.
        scope_match = False
        for tok_candidate in login_list:
            if requested_scopes not in [None, ()]:
                if not self.check_scopes(tok_candidate, requested_scopes):
                    continue
            scope_match = True
            expired = self.get_expired(tok_candidate)
            if not expired:
                return tok_candidate
            else:
                if self.are_refreshable(expired):
                    tok_candidate.update(self.refresh_tokens(expired))
                    self.save_tokens(login_list)
                    return tok_candidate

        if scope_match:
            raise TokensExpired('A previous login matched {} but the tokens '
                                'have expired.'.format(requested_scopes),
                                scopes=requested_scopes)
        else:
            raise ScopesMismatch('No saved tokens match the scopes: {}'
                                 .format(requested_scopes))

    def refresh_tokens(self, tokens):
        """
        Explicitly refresh a token. Called automatically by load_tokens().
        """
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
        """
        Load tokens and create TokenAuthorizers for them. Automatically
        creates a globus_sdk.RefreshTokenAuthorizer if possible, otherwise an
        globus_sdk.AccessTokenAuthorizer. Authorizers are organized by resource
        server. Raises a fair_research_login.exc.LoadError if Token Storage
        is disabled, no tokens were saved, or if the tokens expired or the
        requested scopes don't match. Calls load_tokens() internally.
        **Parameters**
        ``requested_scopes`` (*list*)
          A list of scopes. Example:
          ['openid', 'profile', 'email']
        """
        tokens = self.load_tokens(requested_scopes=requested_scopes)
        explicit_scopes = requested_scopes or self.get_scope_set(tokens)
        authorizers = {}
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
        Revoke saved tokens and clear them from storage. Raises
        fair_research_login.exc.TokenStorageDisabled if no token storage is
        set, otherwise attempts to revoke tokens then returns None.
        """
        for tset in self._load_raw_tokens():
            self.revoke_token_set(tset)
        self.token_storage.clear_tokens()

    def revoke_token_set(self, tokens):
        """
        Revoke Tokens for a given token group.
        **parameters**
          ``tokens`` (*dict*)
          An object matching
          globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
        """
        for rs, tok_set in tokens.items():
            self.client.oauth2_revoke_token(tok_set.get('access_token'))
            self.client.oauth2_revoke_token(tok_set.get('refresh_token'))

    @staticmethod
    def get_scope_set(token_group):
        """
        Returns a list of scopes given a token_group organized by:
        globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
        """
        scopes = [tset['scope'].split() for tset in token_group.values()]
        flat_list = [item for sublist in scopes for item in sublist]
        return flat_list

    @classmethod
    def check_scopes(cls, tokens, requested_scopes):
        """
        Returns true if scopes match the tokens passed in, false otherwise.
        **Parameters**
          ``tokens`` (**dict**)
          A token grouping, organized by:
          globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
          Example:
            {
                'auth.globus.org': {
                    'scope': 'openid profile email',
                    'access_token': '<token>',
                    'refresh_token': None,
                    'token_type': 'Bearer',
                    'expires_at_seconds': 1234567,
                    'resource_server': 'auth.globus.org'
                }, ...
            }
        """
        return set(cls.get_scope_set(tokens)) == set(requested_scopes)

    @staticmethod
    def get_expired(tokens):
        """
        Returns a Token Group organized by:
        globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
        For all tokens in that group that are expired. Ignores whether there
        is a refresh token attached to that token.
        """
        return {rs: tset for rs, tset in tokens.items()
                if time.time() >= tset['expires_at_seconds']}

    @staticmethod
    def are_refreshable(tokens):
        """
        Returns True if all tokens in the group organized by:
        globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
        have refresh tokens. This should always return True with tokens stored
        from a login(refresh_tokens=True).
        """
        return all([bool(ts['refresh_token']) for ts in tokens.values()])
