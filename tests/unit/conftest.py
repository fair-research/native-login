import pytest
import webbrowser
import time
from copy import deepcopy
from .mocks import MemoryStorage, MOCK_TOKEN_SET, MOCK_TOKEN_SET_UNDERSCORES
from fair_research_login import CodeHandler

import globus_sdk
from unittest.mock import Mock


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def refresh_authorizer_raises_invalid_grant(monkeypatch):

    class MockException(Exception):
        status_code = 400
        message = 'invalid_grant'

    monkeypatch.setattr(globus_sdk, 'AuthAPIError', MockException)
    monkeypatch.setattr(globus_sdk.RefreshTokenAuthorizer,
                        'ensure_valid_token',
                        Mock(side_effect=globus_sdk.AuthAPIError()))


@pytest.fixture
def mock_tokens_underscores():
    return deepcopy(MOCK_TOKEN_SET_UNDERSCORES)


@pytest.fixture
def mock_expired_tokens(mock_tokens):
    tokens = deepcopy(mock_tokens)
    for tset in tokens.values():
        tset['expires_at_seconds'] = 0
    return tokens


@pytest.fixture
def expired_tokens_with_refresh(mock_expired_tokens):
    tokens = deepcopy(mock_expired_tokens)
    for tset in tokens.values():
        tset['refresh_token'] = '<Mock Refresh Token>'
    return tokens


@pytest.fixture
def mock_refresh_token_authorizer(monkeypatch, mock_tokens,
                                  mock_token_response):
    def get_new_access_token(self):
        self.access_token = '<Refreshed Access Token>'
        self.expires_at = int(time.time()) + 60 * 60 * 48
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
    monkeypatch.setattr('builtins.input', mock)
    return mock


@pytest.fixture
def mock_webbrowser(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(webbrowser, 'open', mock)
    return mock


@pytest.fixture
def mock_is_remote_session(monkeypatch):
    func_mock = Mock(return_value=False)
    monkeypatch.setattr(CodeHandler, 'is_remote_session', func_mock)
    return func_mock


@pytest.fixture
def mock_revoke(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(globus_sdk.NativeAppAuthClient,
                        'oauth2_revoke_token', mock)
    return mock


@pytest.fixture
def mock_sdk_v2(monkeypatch):
    monkeypatch.setattr(globus_sdk.version, '__version__', '2.0.1')
    return globus_sdk.version.__version__


@pytest.fixture
def mock_sdk_oauth2_get_authorize_url(monkeypatch):
    monkeypatch.setattr(globus_sdk.NativeAppAuthClient,
                        'oauth2_get_authorize_url', Mock())
    return globus_sdk.NativeAppAuthClient.oauth2_get_authorize_url


@pytest.fixture
def mock_token_response(monkeypatch, mock_tokens):
    class GlobusSDKTokenResponse:
        def __init__(self, *args, **kwargs):
            self.tokens = mock_tokens

        @property
        def by_resource_server(self):
            return self.tokens

    monkeypatch.setattr(globus_sdk.NativeAppAuthClient,
                        'oauth2_exchange_code_for_tokens',
                        GlobusSDKTokenResponse)
    return GlobusSDKTokenResponse()
