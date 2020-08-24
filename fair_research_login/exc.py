

class LoginException(Exception):
    pass


class InvalidTokenFormat(LoginException):
    def __init__(self, message, code=None):
        super(InvalidTokenFormat, self).__init__(message)
        self.code = code

    def __str__(self):
        return '({}) {}'.format(super(InvalidTokenFormat, self).__str__(),
                                self.code)


class AuthFailure(LoginException):
    """Authentication with Globus Auth failed for some reason"""
    pass


class LocalServerError(AuthFailure):
    """The Local Server Code Handler failed to get an auth code"""
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

    def __str__(self):
        return '{} {}'.format(
            super(TokensExpired, self).__str__(),
            ', '.join(self.resource_servers)
        )
