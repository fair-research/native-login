from uuid import uuid4
import pytest
from globus_sdk import AccessTokenAuthorizer, RefreshTokenAuthorizer

from fair_research_login.client import NativeClient
from fair_research_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.code_handler import InputCodeHandler
from fair_research_login.exc import (
    LoadError, ScopesMismatch, TokensExpired, NoSavedTokens
)
from fair_research_login.version import __version__


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


def test_logout(mock_revoke, login_token_group, mem_storage):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = login_token_group
    cli.logout()
    assert mock_revoke.call_count == 6


def test_load_tokens(mem_storage, login_token_group):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = login_token_group
    assert cli.load_tokens() == login_token_group[0]


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


def test_load_with_no_saved_tokens(mem_storage):
    mem_storage.tokens = []
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(NoSavedTokens):
        cli.load_tokens()


def test_load_raises_scopes_mismatch(mem_storage, login_token_group):
    cli = NativeClient(client_id=str(uuid4()),
                       token_storage=mem_storage)
    mem_storage.tokens = login_token_group
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


def test_load_resolves_scopes_on_multi_login(
        mem_storage, mock_tokens,
        login_token_group_underscores):
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    mem_storage.tokens = [
        {'auth.globus.org': mock_tokens['auth.globus.org']},
        mock_tokens,
        login_token_group_underscores[0],
    ]
    # None of these should throw errors
    cli.load_tokens(requested_scopes=['rs_w_underscores_scope'])
    cli.load_tokens(requested_scopes=['openid', 'email', 'profile'])
    cli.load_tokens(requested_scopes=[
        'custom_scope', 'urn:globus:auth:scope:transfer.api.globus.org:all',
        'openid', 'email', 'profile'
    ])


def test_client_token_refresh_without_tokens_raises(mock_tokens):
    cli = NativeClient(client_id=str(uuid4()), token_storage=None)
    with pytest.raises(TokensExpired):
        cli.refresh_tokens(mock_tokens)


def test_client_token_refresh_with_tokens(expired_login_with_refresh,
                                          mock_refresh_token_authorizer):
    cli = NativeClient(client_id=str(uuid4()), token_storage=None)
    tokens = cli.refresh_tokens(expired_login_with_refresh[0])
    for tset in tokens.values():
        assert tset['access_token'] == '<Refreshed Access Token>'


def test_client_get_authorizers(login_token_group,
                                mock_refresh_token_authorizer,
                                mem_storage):
    login_token_group[0]['resource.server.org']['refresh_token'] = '<Resh Tok>'
    mem_storage.tokens = login_token_group
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    for rs, authorizer in cli.get_authorizers().items():
        if rs == 'resource.server.org':
            assert isinstance(authorizer, RefreshTokenAuthorizer)
        else:
            assert isinstance(authorizer, AccessTokenAuthorizer)


def test_client_load_auto_refresh(expired_login_with_refresh, mem_storage,
                                  mock_refresh_token_authorizer):
    mem_storage.tokens = expired_login_with_refresh
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    tokens = cli.load_tokens()
    for tset in tokens.values():
        assert tset['access_token'] == '<Refreshed Access Token>'


def test_authorizer_refresh_hook(login_token_group,
                                 mock_refresh_token_authorizer,
                                 mem_storage):
    login_token_group[0]['resource.server.org']['refresh_token'] = '<Ref Tok>'
    mem_storage.tokens = login_token_group
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    rs_auth = cli.get_authorizers()['resource.server.org']
    rs_auth.expires_at = 0
    rs_auth.check_expiration_time()

    tokens = cli.load_tokens()
    assert 'example.on.refresh.success' in tokens.keys()


def test_client_when_cannot_refresh(expired_login_group, mem_storage,
                                    mock_refresh_token_authorizer):
    mem_storage.tokens = expired_login_group
    cli = NativeClient(client_id=str(uuid4()), token_storage=mem_storage)
    with pytest.raises(TokensExpired):
        cli.load_tokens()


# def test_check_expired_with_valid_tokens(mock_tokens):
#     assert check_expired(mock_tokens) is None
#
#
# def test_check_expired(mock_expired_tokens):
#     with pytest.raises(TokensExpired):
#         check_expired(mock_expired_tokens)
#
#
# def test_expired_contains_useful_info(mock_expired_tokens):
#     exc = None
#     try:
#         check_expired(mock_expired_tokens)
#     except TokensExpired as te:
#         exc = te
#     assert exc
#     for token in mock_expired_tokens:
#         assert token in str(exc)
#
#
# def test_check_scopes_with_valid_scopes(mock_tokens):
#     scopes = ['custom_scope', 'profile', 'openid', 'email',
#               'urn:globus:auth:scope:transfer.api.globus.org:all']
#     assert check_scopes(mock_tokens, scopes) is None
