import pytest

from native_login.token_storage import (
    check_expired, check_scopes, flat_pack, flat_unpack
)
from native_login.exc import TokensExpired, ScopesMismatch


def test_check_expired_with_valid_tokens(mock_tokens):
    assert check_expired(mock_tokens) is None


def test_check_expired(mock_expired_tokens):
    with pytest.raises(TokensExpired):
        check_expired(mock_expired_tokens)


def test_expired_contains_useful_info(mock_expired_tokens):
    exc = None
    try:
        check_expired(mock_expired_tokens)
    except TokensExpired as te:
        exc = te
    assert exc
    for token in mock_expired_tokens:
        assert token in str(exc)


def test_check_scopes_with_valid_scopes(mock_tokens):
    scopes = ['custom_scope', 'profile', 'openid', 'email',
              'urn:globus:auth:scope:transfer.api.globus.org:all']
    assert check_scopes(mock_tokens, scopes) is None


def test_check_scopes_with_differing_scopes(mock_tokens):
    with pytest.raises(ScopesMismatch):
        check_scopes(mock_tokens, ['custom_scope'])


def test_flat_pack_unpack(mock_tokens):
    exercised_tokens = flat_unpack(flat_pack(mock_tokens))
    assert exercised_tokens == mock_tokens


def test_flat_unpack_with_empty_value():
    assert flat_unpack({}) == {}
