import pytest
from fair_research_login.exc import LoadError
from fair_research_login.token_storage import (
    flat_pack, flat_unpack
)


def test_flat_pack_unpack(login_token_group):
    exercised_tokens = flat_unpack(flat_pack(login_token_group))
    assert exercised_tokens == login_token_group


def test_flat_unpack_rs_with_underscores(login_token_group_underscores):
    exercised_tokens = flat_unpack(flat_pack(login_token_group_underscores))
    assert exercised_tokens == login_token_group_underscores


def test_flat_unpack_with_empty_value():
    assert flat_unpack([]) == []


def test_flat_pack_invalid_key_names(login_token_group):
    packed = flat_pack(login_token_group)
    packed['foo__bar__baz__bilium'] = 'value'
    with pytest.raises(LoadError):
        flat_unpack(packed)
