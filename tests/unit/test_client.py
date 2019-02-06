from uuid import uuid4
import pytest

from native_login.client import NativeClient
from native_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from native_login.local_server import LocalServerCodeHandler
from native_login.code_handler import InputCodeHandler
from native_login.exc import LoadError


def test_client_login(mock_input, mock_token_response):
    cli = NativeClient(client_id=str(uuid4()),
                       secondary_code_handler=InputCodeHandler())
    assert isinstance(cli.token_storage, MultiClientTokenStorage)
    assert isinstance(cli.local_server_code_handler, LocalServerCodeHandler)

    tokens = cli.login(no_local_server=True, no_browser=True)
    assert mock_input.called
    assert tokens == mock_token_response.by_resource_server


def test_custom_local_server_handler(mock_input, mock_webbrowser,
                                     mock_token_response):
    # Shows handlers are fungible and ANY code handler can be used
    cli = NativeClient(client_id=str(uuid4()),
                       local_server_code_handler=InputCodeHandler())
    cli.login()
    assert mock_input.called


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
