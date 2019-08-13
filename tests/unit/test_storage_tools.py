import json
import pytest

from fair_research_login.token_storage import (
    check_expired, check_scopes, flat_pack, flat_unpack, verify_token_group
)
from fair_research_login.exc import (
    TokensExpired, ScopesMismatch, InvalidTokenFormat
)
from tests.unit.mocks import VALID_TOKENS_FILE, INVALID_TOKENS_FILE


def load_json(filename):
    with open(filename) as fh:
        return json.load(fh)


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


def test_check_scopes_with_never_requested_scope(mock_tokens):
    with pytest.raises(ScopesMismatch):
        check_scopes(mock_tokens, ['never_requested'])


def test_check_scopes_with_differing_scope(mock_tokens):
    assert check_scopes(mock_tokens, ['custom_scope']) is None


def test_valid_test_tokens(mock_tokens, mock_expired_tokens,
                           expired_tokens_with_refresh):
    tokens = list(mock_tokens.values())
    tokens += mock_expired_tokens.values()
    tokens += expired_tokens_with_refresh.values()
    verified = [verify_token_group(tk) for tk in tokens]
    verify_lengths = [len(tk) == 6 for tk in verified]
    assert all(verify_lengths)


@pytest.mark.parametrize('tokens', load_json(VALID_TOKENS_FILE))
def test_valid_tokens(tokens):
    # Each token group should return
    verified = verify_token_group(tokens)
    assert isinstance(verified, dict)
    assert len(verified) == 6


@pytest.mark.parametrize('tokens', load_json(INVALID_TOKENS_FILE))
def test_invalid_tokens(tokens):
    with pytest.raises(InvalidTokenFormat):
        verify_token_group(tokens)


def test_verify_error_includes_code():
    e = InvalidTokenFormat('A Bad Format Was Detected!', code='bad_format')
    assert 'bad_format' in str(e)


def test_flat_pack_unpack(mock_tokens):
    exercised_tokens = flat_unpack(flat_pack(mock_tokens))
    assert exercised_tokens == mock_tokens


def test_flat_unpack_rs_with_underscores(mock_tokens_underscores):
    exercised_tokens = flat_unpack(flat_pack(mock_tokens_underscores))
    assert exercised_tokens == mock_tokens_underscores


def test_flat_unpack_with_empty_value():
    assert flat_unpack({}) == {}
