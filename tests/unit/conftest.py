import pytest
import webbrowser
from copy import deepcopy
from .mocks import MemoryStorage, MOCK_TOKEN_SET
from native_login import NativeClient, client
import six

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
def mock_refresh_token_authorizer(monkeypatch):
    monkeypatch.setattr(client,
                        'RefreshTokenAuthorizer',
                        Mock())


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
            pass

        @property
        def by_resource_server(self):
            return mock_tokens

    monkeypatch.setattr(NativeClient, 'oauth2_exchange_code_for_tokens',
                        GlobusSDKTokenResponse)
    return GlobusSDKTokenResponse()
