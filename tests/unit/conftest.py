import pytest
import webbrowser
import time
from copy import deepcopy
from .mocks import MemoryStorage, MOCK_TOKEN_SET
from native_login import NativeClient
import six

import globus_sdk

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def mock_expired_tokens(mock_tokens):
    for tset in mock_tokens.values():
        tset['expires_at_seconds'] = 0
    return mock_tokens


@pytest.fixture
def expired_tokens_with_refresh(mock_expired_tokens):
    for tset in mock_expired_tokens.values():
        tset['refresh_token'] = '<Mock Refresh Token>'
    return mock_expired_tokens


@pytest.fixture
def mock_refresh_token_authorizer(monkeypatch, mock_tokens,
                                  mock_token_response):
    def get_new_access_token(self):
        self.access_token = '<Refreshed Access Token>'
        self._set_expiration_time(int(time.time()) + 60 * 60 * 48)
        if self.on_refresh is not None:
            # We can't fetch real tokens, so make some up!
            custom_tokens = {'example.on.refresh.success':
                             mock_tokens['resource.server.org']}
            mock_token_response.tokens = custom_tokens
            self.on_refresh(mock_token_response)
    monkeypatch.setattr(globus_sdk.RefreshTokenAuthorizer,
                        '_get_new_access_token',
                        get_new_access_token)


@pytest.fixture
def mock_input(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(six.moves, 'input', mock)
    return mock


@pytest.fixture
def mock_webbrowser(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(webbrowser, 'open', mock)
    return mock


@pytest.fixture
def mock_revoke(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(NativeClient, 'oauth2_revoke_token', mock)
    return mock


@pytest.fixture
def mock_token_response(monkeypatch, mock_tokens):
    class GlobusSDKTokenResponse:
        def __init__(self, *args, **kwargs):
            self.tokens = mock_tokens

        @property
        def by_resource_server(self):
            return self.tokens

    monkeypatch.setattr(NativeClient, 'oauth2_exchange_code_for_tokens',
                        GlobusSDKTokenResponse)
    return GlobusSDKTokenResponse()
