import logging
from fair_research_login.client import NativeClient
from fair_research_login.token_storage import (ConfigParserTokenStorage,
                                               MultiClientTokenStorage,
                                               JSONTokenStorage,
                                               )
from fair_research_login.code_handler import (InputCodeHandler, CodeHandler)
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.exc import (LoginException, LoadError, ScopesMismatch,
                                     TokensExpired, LocalServerError,
                                     AuthFailure)

__all__ = [
    'NativeClient',

    'JSONTokenStorage', 'ConfigParserTokenStorage',
    'MultiClientTokenStorage',

    'CodeHandler', 'InputCodeHandler', 'LocalServerCodeHandler',

    'LoginException', 'LoadError', 'ScopesMismatch', 'TokensExpired',
    'LocalServerError', 'AuthFailure',
]

# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library  # noqa
logging.getLogger("fair_research_login").addHandler(logging.NullHandler())
