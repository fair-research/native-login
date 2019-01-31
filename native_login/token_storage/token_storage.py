import os


class TokenStorage(object):

    DEFAULT_FILENAME = os.path.expanduser('~/.globus-native-apps.cfg')
    TOKEN_KEYS = [
        "scope",
        "access_token",
        "refresh_token",
        "token_type",
        "expires_at_seconds",
        "resource_server",
    ]
    REQUIRED_KEYS = ["scope", "access_token", "expires_at_seconds",
                     "resource_server"]

    def __init__(self, filename=None):
        self.filename = filename or self.DEFAULT_FILENAME

    def write_tokens(self, token_response):
        """

        :param token_response:
        :return:
        """
        raise NotImplemented()

    def read_tokens(self):
        raise NotImplemented()

    def clear_tokens(self):
        raise NotImplemented()

    def serialize_tokens(self, oauth_token_response):
        return oauth_token_response.by_resource_server

    def deserialize_tokens(self, saved_tokens):
        return saved_tokens
