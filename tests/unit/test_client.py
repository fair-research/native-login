from uuid import uuid4
import pytest

from native_login.client import NativeClient
from native_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from native_login.local_server import LocalServerCodeHandler
from native_login.code_handler import InputCodeHandler
from native_login.exc import LoadError, ScopesMismatch
from native_login.version import __version__


def test_version_sanity():
    assert isinstance(__version__, str)


def test_client_defaults():
    cli = NativeClient(client_id=str(uuid4()))
    assert isinstance(cli.token_storage, MultiClientTokenStorage)
    assert isinstance(cli.local_server_code_handler, LocalServerCodeHandler)


def test_client_login(mock_input, mock_webbrowser, mock_token_response,
                      mem_storage):
    cli = NativeClient(client_id=str(uuid4()),
                       local_server_code_handler=InputCodeHandler(),
                       token_storage=mem_storage)

    tokens = cli.login()
    assert mock_input.called
    assert tokens == mock_token_response.by_resource_server


def test_custom_local_server_handler(mock_input, mock_webbrowser,
                                     mock_token_response, mem_storage):
    # Shows handlers are fungible and ANY code handler can be used
    cli = NativeClient(client_id=str(uuid4()),
                       local_server_code_handler=InputCodeHandler(),
                       token_storage=mem_storage)
    cli.login()
    assert mock_input.called


def test_revoke_login(mock_revoke, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()))
    cli.revoke_token_set(mock_tokens)
    assert mock_revoke.call_count == 6


def test_logout(mock_revoke, mock_tokens, mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    cli.logout()
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
        cli.logout()


def test_custom_token_storage():
    class GoodStorage:
        def write_tokens(self, tokens):
            pass

        def read_tokens(self):
            pass

        def clear_tokens(self):
            pass
    NativeClient(client_id=str(uuid4()), token_storage=GoodStorage())


def test_client_raises_attribute_error_bad_token_storage():
    class BadStorage:
        pass
    with pytest.raises(AttributeError):
        NativeClient(client_id=str(uuid4()), token_storage=BadStorage())


def test_login_with_no_storage(mock_input, mock_webbrowser,
                               mock_token_response):
    cli = NativeClient(client_id=str(uuid4()),
                       local_server_code_handler=InputCodeHandler(),
                       token_storage=None)
    tokens = cli.login()
    assert tokens == mock_token_response.by_resource_server


def test_load_raises_scopes_mismatch(mem_storage, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()),
                       token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    with pytest.raises(ScopesMismatch):
        cli.load_tokens(requested_scopes=['foo'])


def test_client_load_errors_silenced_on_login(
        monkeypatch, mem_storage, mock_input, mock_webbrowser,
        mock_token_response):
    def raise_load_error(*args, **kwargs):
        raise LoadError()
    monkeypatch.setattr(mem_storage, 'read_tokens', raise_load_error)
    monkeypatch.setattr(mem_storage, 'write_tokens', raise_load_error)
    cli = NativeClient(client_id=str(uuid4()),
                       local_server_code_handler=InputCodeHandler(),
                       token_storage=None)
    tokens = cli.login()
    assert tokens == mock_token_response.by_resource_server
