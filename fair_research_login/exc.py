

class LoginException(Exception):
    """
    A top level fair_research_login exception, which can be used to catch
    all other exceptions in fair_research_login.
    """
    pass


class InvalidTokenFormat(LoginException):
    """
    A token format was found to be an invalid format.
    """
    def __init__(self, message, code=None):
        super(InvalidTokenFormat, self).__init__(message)
        self.code = code

    def __str__(self):
        return '({}) {}'.format(super(InvalidTokenFormat, self).__str__(),
                                self.code)


class AuthFailure(LoginException):
    """Authentication with Globus Auth failed for some reason."""
    pass


class LocalServerError(AuthFailure):
    """The Local Server Code Handler failed to get an auth code."""
    pass


class LoadError(LoginException):
    """Failed to load tokens from storage."""
    pass


class TokenStorageDisabled(LoadError):
    """
    Storage is disabled and cannot be used, due to no storage being
    configured.
    """
    pass


class NoSavedTokens(LoadError):
    """There were no saved tokens to load."""
    pass


class ScopesMismatch(LoadError):
    """
    Requested scopes do not match loaded scopes.
    """
    pass


class TokensExpired(LoadError):
    """
    Tokens have expired.
    """
    def __init__(self, *args, **kwargs):
        super(TokensExpired, self).__init__(*args)
        self.resource_servers = kwargs.get('resource_servers', ())

    def __str__(self):
        return '{} {}'.format(
            super(TokensExpired, self).__str__(),
            ', '.join(self.resource_servers)
        )
