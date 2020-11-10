from uuid import uuid4
import pytest
from globus_sdk import AccessTokenAuthorizer, RefreshTokenAuthorizer

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from fair_research_login.client import NativeClient
from fair_research_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.code_handler import InputCodeHandler
from fair_research_login.exc import (
    LoadError, ScopesMismatch, TokensExpired, AuthFailure
)
from fair_research_login.version import __version__


def test_version_sanity():
    assert isinstance(__version__, str)


def test_client_defaults():
    cli = NativeClient(client_id=str(uuid4()))
    assert isinstance(cli.token_storage, MultiClientTokenStorage)
    assert isinstance(cli.code_handlers, tuple)
    local_server_handler, input_handler = cli.code_handlers
    assert isinstance(local_server_handler, LocalServerCodeHandler)
    assert isinstance(input_handler, InputCodeHandler)


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


def test_remote_server_fallback(monkeypatch, mock_input, mock_webbrowser,
                                mock_token_response, mem_storage,
                                mock_is_remote_session):
    mock_is_remote_session.return_value = True
    monkeypatch.setattr(LocalServerCodeHandler, 'authenticate', Mock())
    monkeypatch.setattr(InputCodeHandler, 'authenticate', Mock())

    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    cli.login()
    assert mock_is_remote_session.called
    assert not LocalServerCodeHandler.authenticate.called
    assert InputCodeHandler.authenticate.called


def test_login_no_local_server(monkeypatch, mock_input, mock_webbrowser,
                               mock_token_response, mem_storage):
    monkeypatch.setattr(LocalServerCodeHandler, 'authenticate', Mock())
    monkeypatch.setattr(InputCodeHandler, 'authenticate', Mock())

    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    cli.login(no_local_server=True)
    assert not LocalServerCodeHandler.authenticate.called
    assert InputCodeHandler.authenticate.called


def test_code_handler_keyboard_interrupt_skip(monkeypatch, mock_input,
                                              mock_webbrowser, mem_storage,
                                              mock_token_response):
    monkeypatch.setattr(LocalServerCodeHandler, 'authenticate',
                        Mock(side_effect=KeyboardInterrupt()))
    monkeypatch.setattr(InputCodeHandler, 'authenticate', Mock())

    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    cli.login()
    assert InputCodeHandler.authenticate.called


def test_keyboard_interrupt_disables_browser_open(monkeypatch, mock_input,
                                                  mock_webbrowser):
    InputCodeHandler.set_browser_enabled(True)
    is_remote = Mock(return_value=False)
    user_interrupt = Mock(side_effect=KeyboardInterrupt())
    monkeypatch.setattr(InputCodeHandler, 'is_remote_session', is_remote)
    monkeypatch.setattr(InputCodeHandler, 'get_code', user_interrupt)
    cli = NativeClient(client_id=str(uuid4()),
                       code_handlers=[InputCodeHandler(), InputCodeHandler()])
    # Login should open the browser the first time, but not the second.
    with pytest.raises(AuthFailure):
        cli.login()
    assert mock_webbrowser.call_count == 1


def test_code_handler_auth_fail(monkeypatch, mock_input, mock_webbrowser,
                                mock_token_response, mem_storage):
    monkeypatch.setattr(LocalServerCodeHandler, 'authenticate',
                        Mock(return_value=None))
    monkeypatch.setattr(InputCodeHandler, 'authenticate',
                        Mock(return_value=None))

    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(AuthFailure):
        cli.login()


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


def test_load_tokens_by_scope(mem_storage, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    tokens = cli.load_tokens_by_scope()
    assert len(tokens) == 5
    assert set(tokens.keys()) == {
        'openid', 'profile', 'email', 'custom_scope',
        'urn:globus:auth:scope:transfer.api.globus.org:all'
    }


def test_load_no_tokens_raises_error(mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(LoadError):
        cli.load_tokens()


def test_save_tokens(mem_storage, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = {}
    cli.save_tokens(mock_tokens)
    assert mem_storage.tokens == mock_tokens


def test_save_new_tokens(mem_storage, mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = {}
    ts1 = {'auth.globus.org': mock_tokens['auth.globus.org']}
    ts2 = {'transfer.api.globus.org': mock_tokens['transfer.api.globus.org']}
    cli.save_tokens(ts1)
    cli.save_tokens(ts2)
    expected = {'auth.globus.org', 'transfer.api.globus.org'}
    assert set(mem_storage.tokens.keys()) == expected


def test_save_overwrite_scope(mem_storage, mock_tokens, mock_revoke):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = {}
    ts1 = {'auth.globus.org': mock_tokens['auth.globus.org']}
    ts2 = {'auth.globus.org': ts1['auth.globus.org'].copy()}
    ts2['auth.globus.org']['scope'] = 'openid profile'
    # A new scope will come with new access tokens, so ensure those change too
    ts2['auth.globus.org']['access_token'] = 'new_acc'
    ts2['auth.globus.org']['refresh_token'] = 'new_ref'
    ts2['auth.globus.org']['expires_at_seconds'] = (
        ts2['auth.globus.org']['expires_at_seconds'] + 10)
    cli.save_tokens(ts1)
    cli.save_tokens(ts2)
    assert mem_storage.tokens['auth.globus.org']['scope'] == 'openid profile'
    assert mem_storage.tokens['auth.globus.org']['access_token'] == 'new_acc'
    assert mem_storage.tokens['auth.globus.org']['refresh_token'] == 'new_ref'


def test_save_overwrite_tokens(mem_storage, mock_tokens, mock_revoke):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = {}
    ts1 = {'auth.globus.org': mock_tokens['auth.globus.org']}
    ts2 = {'auth.globus.org': ts1['auth.globus.org'].copy()}
    ts2['auth.globus.org']['access_token'] = 'new_acc'
    ts2['auth.globus.org']['refresh_token'] = 'new_ref'
    ts2['auth.globus.org']['expires_at_seconds'] = (
        ts2['auth.globus.org']['expires_at_seconds'] + 10)
    cli.save_tokens(ts1)
    cli.save_tokens(ts2)
    assert mem_storage.tokens['auth.globus.org']['access_token'] == 'new_acc'
    assert mem_storage.tokens['auth.globus.org']['refresh_token'] == 'new_ref'


def test_login_revokes_old_live_token(mock_revoke, mock_tokens, mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = {'auth.globus.org': mock_tokens['auth.globus.org']}
    new_tokens = {'auth.globus.org': mock_tokens['auth.globus.org'].copy()}
    # Mock new login 10 seconds after the first one
    new_tokens['auth.globus.org']['access_token'] = 'new_ac'
    new_tokens['auth.globus.org']['expires_at_seconds'] += 10
    cli.save_tokens(new_tokens)

    assert mock_revoke.call_count == 1


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
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    with pytest.raises(ScopesMismatch):
        cli.load_tokens(requested_scopes=['foo'])


def test_load_tokens_with_invalid_refresh_token(
        mem_storage, expired_tokens_with_refresh,
        refresh_authorizer_raises_invalid_grant):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = expired_tokens_with_refresh
    with pytest.raises(TokensExpired):
        cli.load_tokens()


def test_load_accepts_string_or_iterable_requested_scopes(mem_storage,
                                                          mock_tokens):
    cli = NativeClient(client_id=str(uuid4()),
                       token_storage=mem_storage)
    mem_storage.tokens = mock_tokens
    scopes = ('openid profile email custom_scope '
              'urn:globus:auth:scope:transfer.api.globus.org:all')
    tokens = cli.load_tokens(scopes)
    assert len(tokens) == 3
    authorizers = cli.get_authorizers(scopes)
    assert len(authorizers) == 3


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


def test_client_token_refresh_without_tokens_raises(mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=None)
    with pytest.raises(TokensExpired):
        cli.refresh_tokens(mock_tokens)


def test_client_token_refresh_with_tokens(expired_tokens_with_refresh,
                                          mock_refresh_token_authorizer):
    cli = NativeClient(client_id=str(uuid4()), token_storage=None)
    tokens = cli.refresh_tokens(expired_tokens_with_refresh)
    for tset in tokens.values():
        assert tset['access_token'] == '<Refreshed Access Token>'


def test_client_token_refresh_with_requested_scope_subset(
                                    mem_storage, expired_tokens_with_refresh,
                                    mock_refresh_token_authorizer):
    mem_storage.tokens = expired_tokens_with_refresh
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    tokens = cli.load_tokens(requested_scopes=['profile'])
    assert tokens
    for tset in mem_storage.tokens.values():
        if tset['resource_server'] == 'auth.globus.org':
            assert tset['access_token'] == '<Refreshed Access Token>'
        else:
            assert tset['access_token'] != '<Refreshed Access Token>'


def test_client_get_authorizers(mock_tokens,
                                mock_refresh_token_authorizer,
                                mem_storage):
    mock_tokens['resource.server.org']['refresh_token'] = '<Refresh Token>'
    mem_storage.tokens = mock_tokens
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    for rs, authorizer in cli.get_authorizers().items():
        if rs == 'resource.server.org':
            assert isinstance(authorizer, RefreshTokenAuthorizer)
        else:
            assert isinstance(authorizer, AccessTokenAuthorizer)


def test_client_get_authorizers_by_scope(mock_tokens,
                                         mock_refresh_token_authorizer,
                                         mem_storage):
    mock_tokens['resource.server.org']['refresh_token'] = '<Refresh Token>'
    mem_storage.tokens = mock_tokens
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    by_scope = cli.get_authorizers_by_scope()
    assert len(by_scope) == 5
    for scope, authorizer in by_scope.items():
        if scope == 'custom_scope':
            assert isinstance(authorizer, RefreshTokenAuthorizer)
        else:
            assert isinstance(authorizer, AccessTokenAuthorizer)


def test_client_load_auto_refresh(expired_tokens_with_refresh, mem_storage,
                                  mock_refresh_token_authorizer):
    mem_storage.tokens = expired_tokens_with_refresh
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    tokens = cli.load_tokens()
    for tset in tokens.values():
        assert tset['access_token'] == '<Refreshed Access Token>'


def test_authorizer_refresh_hook(mock_tokens,
                                 mock_refresh_token_authorizer,
                                 mem_storage):
    mock_tokens['resource.server.org']['refresh_token'] = '<Refresh Token>'
    mem_storage.tokens = mock_tokens
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    rs_auth = cli.get_authorizers()['resource.server.org']
    rs_auth.expires_at = 0
    rs_auth.check_expiration_time()

    tokens = cli.load_tokens()
    assert 'example.on.refresh.success' in tokens.keys()


def test_client_when_cannot_refresh(mock_expired_tokens, mem_storage,
                                    mock_refresh_token_authorizer):
    mem_storage.tokens = mock_expired_tokens
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(TokensExpired):
        cli.load_tokens()


def test_non_requested_token_does_not_cancel_load(mem_storage, mock_tokens,
                                                  mock_expired_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    good = ['openid', 'profile',
            'urn:globus:auth:scope:transfer.api.globus.org:all']
    exp = 'custom_scope'
    exprs = 'resource.server.org'
    mem_storage.tokens = mock_tokens
    mem_storage.tokens[exprs] = mock_expired_tokens[exprs]

    # should not raise
    cli.load_tokens(requested_scopes=good)
    cli.load_tokens()
    with pytest.raises(TokensExpired):
        cli.load_tokens(requested_scopes=exp)
