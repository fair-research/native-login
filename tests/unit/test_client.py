from uuid import uuid4
import pytest

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from native_login.client import NativeClient
from native_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from native_login.local_server import LocalServerCodeHandler
from native_login.code_handler import CodeHandler
from native_login.exc import LoadError


@pytest.fixture
def mock_code_handler():
    class MockCodeHandler(CodeHandler):
        def get_code(self):
            return 'mock_code'
    return MockCodeHandler()


@pytest.fixture
def mock_token_response(monkeypatch):
    class GlobusSDKTokenResponse:
        def __init__(self, *args, **kwargs):
            pass

        @property
        def by_resource_server(self):
            return {'my_resource_server': {}}

    monkeypatch.setattr(NativeClient, 'oauth2_exchange_code_for_tokens',
                        GlobusSDKTokenResponse)
    return GlobusSDKTokenResponse()


@pytest.fixture
def mock_revoke(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(NativeClient, 'oauth2_revoke_token', mock)
    return mock


def test_client_login(mock_code_handler, mock_token_response):
    cli = NativeClient(client_id=str(uuid4()),
                       secondary_code_handler=mock_code_handler)
    assert isinstance(cli.token_storage, MultiClientTokenStorage)
    assert isinstance(cli.local_server_code_handler, LocalServerCodeHandler)

    tokens = cli.login(no_local_server=True, no_browser=True)
    assert tokens == mock_token_response.by_resource_server


def test_revoke_login(mock_revoke, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()))
    cli.revoke_token_set(mock_tokens)
    assert mock_revoke.call_count == 6


def test_revoke_saved_tokens(mock_revoke, mock_tokens, mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    cli.revoke_tokens()
    assert mock_revoke.call_count == 6


def test_load_tokens(mem_storage, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    assert cli.load_tokens() == mock_tokens


def test_load_no_tokens_raises_error(mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(LoadError):
        cli.load_tokens()


def test_client_token_calls_with_no_storage_raise_error(mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=None)
    with pytest.raises(LoadError):
        cli.load_tokens()
    with pytest.raises(LoadError):
        cli.save_tokens(mock_tokens)
    with pytest.raises(LoadError):
        cli.revoke_tokens()
