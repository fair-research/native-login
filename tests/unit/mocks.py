import time

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
