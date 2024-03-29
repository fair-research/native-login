import logging
import globus_sdk

from typing import List, Mapping, Union
from fair_research_login.code_handler import InputCodeHandler
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.token_storage import (
    MultiClientTokenStorage, check_expired, check_scopes,
    verify_token_group, get_scopes
)
from fair_research_login.exc import (
    LoadError, TokensExpired, TokenStorageDisabled, NoSavedTokens, AuthFailure
)

log = logging.getLogger(__name__)


sdk_authorizer = Union[globus_sdk.AccessTokenAuthorizer,
                       globus_sdk.RefreshTokenAuthorizer]


class NativeClient(object):
    r"""
    The Native Client serves as another small layer on top of the Globus SDK
    to automatically handle token storage and provide a customizable
    Local Server. It can be used both by simple scripts to simplify the
    auth flow, or by full command line clients that may extend various pieces
    and tailor them to its own needs.

    An example is below:

    .. code-block:: python

        cli = NativeClient(client_id='my_id', app_name='my cool app')
        cli.login(requested_scopes=['openid', 'profile', 'email'])

    :param client_id: The id for your app. Register one at
      https://developers.globus.org
    :type client_id: str
    :param app_name: The name of your app. Shows up on the named grant during
        consent, and the local server browser page by default. It is also
        propogated to globus_sdk.NativeAppAuthClient.
    :type app_name: str
    :param default_scopes: A list of scopes which will serve as the default
        to login() if login is called with no requested_scopes parameter.

        .. code-block:: json

            ["openid", "profile", "email"]

    :type default_scopes: list
    :param token_storage: (*object*)
        Any object capable of reading/writing/clearing tokens from/to disk.
        The object must define these three methods: read_tokens(),
        write_tokens(tokens), and clear_tokens(), where ``tokens`` is a list
        of login groups (dicts), each of which contains a token group (dict)
        keyed by resource server.

        .. code-block:: json

            [
                {
                    "auth.globus.org": {
                        "scope": "openid profile email",
                        "access_token": "<token>",
                        "refresh_token": null,
                        "token_type": "Bearer",
                        "expires_at_seconds": 1234567,
                        "resource_server": "auth.globus.org"
                    }
                }
            ]

        A default token storage object is provided
        at fair_research_login.token_storage.MultiClientTokenStorage, which
        saves tokens in a section named by your clients ``client_id``. None
        may be used to disable token storage.
    :type token_storage: TokenStorage
    :param code_handlers: (*list* of :class:`CodeHandler \
        <fair_research_login.code_handler.CodeHandler>`)
        A list of Code handlers capable of fetching and returning the
        authorization code generated as a browser query param in Globus Auth
        Code handlers are executed in the order they appear in the list, and
        may be skipped by users with ^C or if they cannot be run (Local
        Server Code Handler cannot run on remote servers, for example).
    :type code_handlers:
    """

    TOKEN_STORAGE_ATTRS = {'write_tokens', 'read_tokens', 'clear_tokens'}

    def __init__(self, token_storage=MultiClientTokenStorage(),
                 local_server_code_handler=None,
                 secondary_code_handler=None,
                 code_handlers=(LocalServerCodeHandler(), InputCodeHandler()),
                 default_scopes=None,
                 *args, **kwargs):
        self.client = globus_sdk.NativeAppAuthClient(*args, **kwargs)
        self.token_storage = token_storage
        if token_storage is not None:
            self.verify_token_storage(self.token_storage)
        self.app_name = kwargs.get('app_name') or 'My App'
        if local_server_code_handler or secondary_code_handler:
            log.warning('Specifying "local_server_code_handler" or '
                        '"code_handler" will be removed. Instead, specify '
                        'handlers in a list with keyword "code_handlers"')
            self.code_handlers = [
                    local_server_code_handler or LocalServerCodeHandler(),
                    secondary_code_handler or InputCodeHandler()
                ]
        else:
            self.code_handlers = code_handlers
        log.debug('Using code handlers {}'.format(self.code_handlers))
        if isinstance(self.token_storage, MultiClientTokenStorage):
            self.token_storage.set_client_id(kwargs.get('client_id'))
        log.debug('Token storage set to {}'.format(self.token_storage))
        log.debug('Automatically open browser: {}'
                  ''.format(InputCodeHandler.is_browser_enabled()))
        self.default_scopes = default_scopes

    def login(self,
              requested_scopes: List[str] = None,
              refresh_tokens: bool = None,
              force: bool = False,
              prefill_named_grant: bool = None,
              query_params: dict = None,
              additional_params: dict = None,
              **kwargs):
        r"""
        Do a Native App Auth Flow to get tokens for requested scopes. This
        first attempts to load tokens and will simply return those if they are
        valid, and will automatically attempt to save tokens on login success
        (token_storage must be set for automatic load/save functionality).
        See ``load_tokens`` for how it handles requested_scopes.

        :param requested_scopes: A list of scopes to request of Globus Auth
          during login.

           .. code-block:: json

              ["openid", "profile", "email"]

        :type list:
        :param refresh_tokens: Ask for Globus Refresh Tokens to extend login
            time.
        :type bool:
        :param no_local_server: Disable spinning up a local server to
          automatically copy-paste the auth code. This is automatically
          disabled if the detected session is an SSH session. When used
          locally with no_local_server=False, the domain is localhost
          with a randomly chosen open port number.
        :type bool:
        :param force:
          Force a login flow, even if loaded tokens are valid.
        :type bool:
        :param no_browser: Do not automatically open the browser for the
          Globus Auth URL. Display the URL instead and let the user navigate
          to that location.
        :type bool:
        :param prefill_named_grant: Use a custom named grant on the consent
          page
        :type str:
        :param query_params: Additional Params used in constructing the
          authorize URL for Globus Auth. Used for requesting additional
          features such as for using Globus Sessions. Changed from
          ``additional_params`` in Globus SDK v2
        :type dict:
        :param additional_params: Additional Params used in constructing the
          authorize URL for Globus Auth. Used for requesting additional
          features such as for using Globus Sessions. Deprecated. Use
          ``query_params`` instead.
        :type dict:
        """
        if force is False:
            try:
                return self.load_tokens(requested_scopes=requested_scopes)
            except LoadError as le:
                # Log the specific type of exception along with any message.
                # This gives the user extra info on why a login flow was
                # started. The typical reason is expiration, which looks like
                # this: TokensExpired: auth.globus.org, transfer.api.globus.org
                log.info('{}: {}'.format(le.__class__.__name__, str(le)))

        if additional_params is not None:
            log.warning('login(): "additional_params" is deprecated. '
                        'Please use "query_params" instead.')
            query_params = additional_params

        auth_code = self.get_code(requested_scopes, refresh_tokens,
                                  prefill_named_grant, query_params,
                                  **kwargs)
        token_response = self.client.oauth2_exchange_code_for_tokens(auth_code)
        try:
            self.save_tokens(token_response.by_resource_server)
        except TokenStorageDisabled:
            log.info('Storage disabled, tokens will not be saved.')
        return token_response.by_resource_server

    def get_code(self, requested_scopes, refresh_tokens, prefill_named_grant,
                 query_params, **kwargs):
        """Attempt all configured code handlers in self.code_handlers from
        first to last. If one is not available (local server will not run
        if it detects it is on a remote connection), the next one in the list
        will run. Additionally, if the user enters ^C to interrupt, the code
        handler is skipped and the next one in the list is called. If no
        code handlers remain, an exc.AuthFailure exception is raised.

        Do not call directly. Called indirectly by `login()`. Any additional
        ``kwargs`` passed to login will be passed to each login handler.
        """
        grant_name = prefill_named_grant or '{} Login'.format(self.app_name)
        oauth2_args = dict(
            requested_scopes=requested_scopes or self.default_scopes,
            refresh_tokens=refresh_tokens,
            prefill_named_grant=grant_name,
        )

        for ch in self.code_handlers:
            ch.set_context(self, **kwargs)
            if not ch.is_available():
                log.debug('{} code handler not available.'.format(ch))
                continue
            with ch.start():
                log.debug('Starting code handler {}'.format(ch))
                self.client.oauth2_start_flow(
                    redirect_uri=ch.get_redirect_uri(),
                    **oauth2_args
                )
                auth_url = self.client.oauth2_get_authorize_url(
                    query_params=query_params
                )

                try:
                    auth_code = ch.authenticate(url=auth_url)
                    if auth_code:
                        log.debug('Retrieval of auth code successful!')
                        return auth_code
                except KeyboardInterrupt:
                    # Reattempt with the next handler if this one failed.
                    continue
        raise AuthFailure('Failed to get an auth_code from Globus Auth.')

    def verify_token_storage(self, obj):
        """
        Internal. Verify object passed for token_storage is valid.
        """
        for attr in self.TOKEN_STORAGE_ATTRS:
            if getattr(obj, attr, None) is None:
                raise AttributeError('token_storage requires object "{}" to '
                                     'have the {} attribute'.format(obj, attr))

    def save_tokens(self, tokens: Mapping[str, Mapping]):
        r"""
        Save tokens if token_storage is set. Typically this is called
        automatically in a successful login(). Returns a value from the
        token_storage backend.

        :param tokens: A dict of token dicts, each containing a dict defined by
          globus_sdk.auth.token_response.OAuthTokenResponse\
          .by_resource_server.

            .. code-block:: json

                {
                    "auth.globus.org": {
                        "scope": "profile openid email",
                        "access_token": "<token>",
                        "refresh_token": null,
                        "token_type": "Bearer",
                        "expires_at_seconds": 1539984535,
                        "resource_server": "auth.globus.org"
                    }
                }
        :type dict:
        """
        if self.token_storage is None:
            raise TokenStorageDisabled()

        new_tokens = {rs: verify_token_group(ts) for rs, ts in tokens.items()}
        original_tks = {rs: verify_token_group(ts)
                        for rs, ts, in self._load_raw_tokens().items()}
        original_tks.update(new_tokens)
        return self.token_storage.write_tokens(original_tks)

    def _load_raw_tokens(self):
        """
        Loads tokens without checking whether they have expired. Sorts them by
        expiration time.
        """
        if self.token_storage is not None:
            return self.token_storage.read_tokens() or {}
        raise TokenStorageDisabled('No token_storage set on client.')

    def load_tokens(
        self,
        requested_scopes: List[str] = None
    ) -> Mapping[str, Mapping]:
        """
        Load saved tokens and return them keyed by resource server. If no
        requested_scopes are requested, will attempt to return all active
        tokens, automatically refreshing expired tokens where possible.

        If requested_scopes are provided, load_tokens will guarantee only those
        scopes are returned and that the tokens have not expired (Note: Tokens
        can still be invalid if the user rescind consent). If the tokens have
        expired, a TokensExpired exception is raised. If loaded scopes do
        not contain requested_scopes, a ScopesMismatch exception is raised.

        :param requested_scopes: A list of scopes which must be successfully
          loaded, or a ScopesMismatch error will be raised
        :type: list
        :returns: A dict of token dicts, each containing a dict defined by
           globus_sdk.auth.token_response.OAuthTokenResponse\
           .by_resource_server

           An example looks like the following

           .. code-block:: json

                {
                    "auth.globus.org": {
                        "scope": "profile openid email",
                        "access_token": "<token>",
                        "refresh_token": null,
                        "token_type": "Bearer",
                        "expires_at_seconds": 1539984535,
                        "resource_server": "auth.globus.org"
                    },
                }

        :type dict:
        :raises fair_research_login.exc.NoSavedTokens: If
            no tokens can be loaded
        :raises fair_research_login.exc.TokensExpired: If
            no unexpired tokens could be loaded, or if any requested scopes
            have expired and cannot be refreshed
        :raises fair_research_login.exc.ScopesMismatch: If
            any requested_scopes are missing
        """
        tokens = {rs: verify_token_group(ts) for rs, ts in
                  self._load_raw_tokens().items()}

        if not tokens:
            raise NoSavedTokens('No tokens were loaded')

        if requested_scopes:
            # Support both string and list for requested scope. But ensure
            # it is a list.
            if isinstance(requested_scopes, str):
                requested_scopes = requested_scopes.split(' ')
            requested_scopes = set(requested_scopes)
            # Ensure only requested tokens are used.
            tokens = {rs: ts for rs, ts in tokens.items()
                      if requested_scopes.intersection(ts['scope'].split())}
            # Ensure all requested tokens are present.
            check_scopes(tokens, requested_scopes)

        try:
            check_expired(tokens)
        except TokensExpired as te:
            expired = {rs: tokens[rs] for rs in te.resource_servers}
            # If the user requested scopes, one of their scopes expired by this
            # point and we need to let them know.
            if requested_scopes and not self._refreshable(expired):
                raise
            # At this point, scopes expired but either were refreshable, or
            # the user didn't specify.
            refreshed = self.refresh_tokens(self.get_refreshable(expired))
            self.save_tokens(refreshed)
            unexpired = {rs: ts for rs, ts in tokens.items()
                         if rs not in expired}
            unexpired.update(refreshed)
            tokens = unexpired
            if not tokens:
                raise

        return tokens

    def get_refreshable(self, tokens):
        return {t: ts for t, ts in tokens.items() if bool(ts['refresh_token'])}

    def _refreshable(self, tokens):
        return all([bool(ts['refresh_token']) for ts in tokens.values()])

    def load_tokens_by_scope(self, requested_scopes: List[str] = None):
        """
        Like load_tokens(), but returns a dict keyed by token scopes
        instead of by resource server. If there are multiple scopes requested
        for the same token (such as ['openid', 'profile', 'email']), each
        scope will have a duplicate copy of the same information.

        :param requested_scopes: A list of scopes which must be successfully
          loaded, or a ScopesMismatch error will be raised
        :type list:
        :raises fair_research_login.exc.NoSavedTokens: If no tokens can be
            loaded
        :raises fair_research_login.exc.TokensExpired: If no unexpired
            tokens could be loaded, or if any requested scopes have expired
            and cannot be refreshed
        :raises fair_research_login.exc.ScopesMismatch: If requested_scopes
            are missing
        """
        tokens = self.load_tokens(requested_scopes)
        token_group = {}
        for scope in get_scopes(tokens):
            for tgroup in tokens.values():
                if scope in tgroup['scope'].split():
                    token_group[scope] = tgroup
        return token_group

    def refresh_tokens(self, tokens):
        """
        Explicitly refresh a token. Called automatically by load_tokens().
        """
        if not self._refreshable(tokens):
            raise TokensExpired('No Refresh Token, cannot refresh tokens: ',
                                resource_servers=tokens.keys())

        for rs, token_dict in tokens.items():
            authorizer = globus_sdk.RefreshTokenAuthorizer(
                token_dict['refresh_token'],
                self.client,
                access_token=token_dict['access_token'],
                expires_at=token_dict['expires_at_seconds'],
            )
            try:
                authorizer.ensure_valid_token()
                token_dict['access_token'] = authorizer.access_token
                token_dict['expires_at_seconds'] = authorizer.expires_at
            except globus_sdk.AuthAPIError as aapie:
                if aapie.message == 'invalid_grant':
                    raise TokensExpired('Refresh Token Expired: ',
                                        resource_servers=[rs])
        return tokens

    def get_authorizer(self, token_dict: Mapping[str, str]
                       ) -> Mapping[str, sdk_authorizer]:
        """
        Create an authorizer for a given dict of tokens. Returns a
        globus_sdk.RefreshTokenAuthorizer if there is a refresh token, else
        a globus_sdk.AccessTokenAuthorizer. Tokens are not checked for
        expiration or validity.
        Example token dict would produce a RefreshTokenAuthorizer:

        .. code-block:: json

            {
                "scope": "profile openid email",
                "access_token": "<token>",
                "refresh_token": <token>,
                "expires_at_seconds": 1539984535
            }

        :param token_dict: A dictionary containing access_token information
        :type dict:
        :returns: The dict with original keys, with values being authorizers.
            RefreshTokenAuthorizers are preferred if possible
        :raises fair_research_login.exc.NoSavedTokens: If no tokens can be
            loaded
        :raises fair_research_login.exc.TokensExpired: If no unexpired tokens
            could be loaded, or if any requested scopes
            have expired and cannot be refreshed
        :raises fair_research_login.exc.ScopesMismatch: If requested_scopes
            are missing
        """
        if token_dict.get('refresh_token') is not None:
            return globus_sdk.RefreshTokenAuthorizer(
                token_dict['refresh_token'],
                self.client,
                access_token=token_dict['access_token'],
                expires_at=token_dict['expires_at_seconds'],
                on_refresh=self.on_refresh,
            )
        else:
            return globus_sdk.AccessTokenAuthorizer(token_dict['access_token'])

    def get_authorizers(self, requested_scopes: List[str] = None
                        ) -> Mapping[str, sdk_authorizer]:
        """
        Load tokens and create TokenAuthorizers for them. Automatically
        creates a globus_sdk.RefreshTokenAuthorizer if possible, otherwise an
        globus_sdk.AccessTokenAuthorizer. Authorizers are organized by resource
        server. Raises a fair_research_login.exc.LoadError if Token Storage
        is disabled, no tokens were saved, or if the tokens expired or the
        requested scopes don't match. Calls load_tokens() internally.

        :param requested_scopes: A list of scopes which must be successfully
            loaded, or a ScopesMismatch error will be raised
        :returns: The dict keyed by resource server, with values being
            authorizers. RefreshTokenAuthorizers are preferred if possible
        :raises fair_research_login.exc.NoSavedTokens: If no tokens can be
            loaded
        :raises fair_research_login.exc.TokensExpired: If no unexpired
            tokens could be loaded, or if any requested scopes have expired and
            cannot be refreshed
        :raises fair_research_login.exc.ScopesMismatch: If requested_scopes are
            missing
        """
        tokens = self.load_tokens(requested_scopes=requested_scopes)
        return {rs: self.get_authorizer(ts) for rs, ts in tokens.items()}

    def get_authorizers_by_scope(self, requested_scopes: List[str] = None):
        """
        Like get_authorizers(), but returns a dict keyed by scope rather than
        by resource server.

        :param requested_scopes: A list of scopes which must be successfully
            loaded, or a ScopesMismatch error will be raised
        :returns: The dict of authorizers keyed by scope, with values being
            authorizers. RefreshTokenAuthorizers are preferred if possible
        :raises fair_research_login.exc.NoSavedTokens: If no tokens can be
            loaded
        :raises fair_research_login.exc.TokensExpired: If no unexpired tokens
            could be loaded, or if any requested scopes have expired and cannot
            be refreshed
        :raises fair_research_login.exc.ScopesMismatch: If requested_scopes
            are missing
        """
        tokens = self.load_tokens_by_scope(requested_scopes)
        return {scope: self.get_authorizer(tokens)
                for scope, tokens in tokens.items()}

    def on_refresh(self, token_response):
        loaded_tokens = self._load_raw_tokens()
        loaded_tokens.update(token_response.by_resource_server)
        self.save_tokens(loaded_tokens)

    def logout(self):
        """
        Revoke saved tokens and clear them from storage. Raises
        fair_research_login.exc.TokenStorageDisabled if no token storage is
        set, otherwise attempts to revoke tokens then returns None.

        Clients NOT using token storage should use 'revoke_token_set' instead
        to revoke tokens.
        """
        self.revoke_token_set(self._load_raw_tokens())
        self.token_storage.clear_tokens()

    def revoke_token_set(self, tokens):
        """
        Revoke Tokens for a given token group.

        :param tokens: A dict of tokens to revoke
          An object matching
          globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server

          .. code-block:: json

            {
                "auth.globus.org": {
                    "scope": "profile openid email",
                    "access_token": "<token>",
                    "refresh_token": null,
                    "token_type": "Bearer",
                    "expires_at_seconds": 1539984535,
                    "resource_server": "auth.globus.org"
                }
            }
        """
        for rs, tok_set in tokens.items():
            self.client.oauth2_revoke_token(tok_set.get('access_token'))
            self.client.oauth2_revoke_token(tok_set.get('refresh_token'))
