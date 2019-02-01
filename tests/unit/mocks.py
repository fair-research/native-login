import time
from native_login import TokenStorage

DEFAULT_EXPIRE = time.time() + 60 * 60 * 48


MOCK_TOKEN_SET = {
    'resource.server.org': {
        'scope': 'profile openid email',
        'access_token': '<token>',
        'refresh_token': None,
        'token_type': 'Bearer',
        'expires_at_seconds': DEFAULT_EXPIRE,
        'resource_server': 'resource.server.org'
    }
}


class MemoryStorage(TokenStorage):
    def __init__(self):
        super(MemoryStorage, self).__init__()
        self.tokens = {}

    def write_tokens(self, tokens):
        self.tokens = tokens

    def read_tokens(self):
        return self.tokens

    def clear_tokens(self):
        self.tokens = {}
