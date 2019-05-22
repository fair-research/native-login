

class LoginException(Exception):
    pass


class LocalServerError(LoginException):
    pass


class LoadError(LoginException):
    pass


class TokenStorageDisabled(LoadError):
    pass


class NoSavedTokens(LoadError):
    """There were no saved tokens to load"""
    pass


class ScopesMismatch(LoadError):
    """
    Requested scopes do not match loaded scopes
    """
    pass


class TokensExpired(LoadError):
    """
    Tokens have expired
    """
    def __init__(self, *args, **kwargs):
        super(TokensExpired, self).__init__(*args)
        self.resource_servers = kwargs.get('resource_servers', ())
        self.scopes = kwargs.get('scopes', ())

    def __str__(self):
        return '{} {}'.format(
            super(TokensExpired, self).__str__(), ', '.join(self.scopes)
        )
