import time
import os


DATA_PATH = os.path.join(os.path.dirname(__file__), 'data')
CONFIGPARSER_VALID_CFG = os.path.join(DATA_PATH, 'configparser_valid.cfg')
VALID_TOKENS_FILE = os.path.join(DATA_PATH, 'valid_tokens.json')
INVALID_TOKENS_FILE = os.path.join(DATA_PATH, 'invalid_tokens.json')

DEFAULT_EXPIRE = int(time.time()) + 60 * 60 * 48


MOCK_TOKEN_SET = {
    'auth.globus.org': {
        'scope': 'openid profile email',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'auth.globus.org'
    },
    'transfer.api.globus.org': {
        'scope': 'urn:globus:auth:scope:transfer.api.globus.org:all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'transfer.api.globus.org'
    },
    'resource.server.org': {
        'scope': 'custom_scope',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'resource.server.org'
    }
}

MOCK_TOKEN_SET_UNDERSCORES = {
    'resource_server_with_underscores': {
        'scope': 'all',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'resource_server_with_underscores'
    }
}


class MemoryStorage(object):
    def __init__(self):
        super(MemoryStorage, self).__init__()
        self.tokens = {}

    def write_tokens(self, tokens):
        self.tokens = tokens

    def read_tokens(self):
        return self.tokens

    def clear_tokens(self):
        self.tokens = {}
