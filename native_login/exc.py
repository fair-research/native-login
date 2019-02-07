

class LoginException(Exception):
    pass


class LocalServerError(LoginException):
    pass


class LoadError(LoginException):
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
    def __init__(self, *args, resource_servers=(), **kwargs):
        super(TokensExpired, self).__init__(*args, **kwargs)
        self.resource_servers = resource_servers

    def __str__(self):
        return '{} {}'.format(
            super(TokensExpired, self).__str__(),
            ', '.join(self.resource_servers)
        )
