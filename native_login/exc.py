

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
    pass
