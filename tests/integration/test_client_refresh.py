
"""
The most basic usage automatically saves and loads tokens, and provides
a local server for logging in users.
"""
import pytest


@pytest.mark.skip(reason='Integration test')
def test_refresh(live_client):
    tokens = live_client.login(refresh_tokens=True)
    for tset in tokens.values():
        tset['expires_at_seconds'] = 0
    live_client.save_tokens(tokens)
    for rs, new_tokens in live_client.load_tokens().items():
        assert tokens[rs]['access_token'] != new_tokens['access_token']


@pytest.mark.skip(reason='Integration test')
def test_authorizer_refresh_hook(live_client):
    tokens = live_client.login(refresh_tokens=True)
    old_access_token = tokens['auth.globus.org']['access_token']

    auth = live_client.get_authorizers()['auth.globus.org']
    old_auth_tok = auth.access_token
    auth.expires_at = 0
    auth.check_expiration_time()

    saved_token = live_client.load_tokens()['auth.globus.org']['access_token']
    assert old_auth_tok != auth.access_token
    assert saved_token == auth.access_token
    assert saved_token != old_access_token
