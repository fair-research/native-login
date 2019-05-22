
"""
Tests real usage of the tool, for some things that can't be tested via mocking.

Enable by setting:
export SKIP_INTEGRATION_TESTS=False
"""
import os
import pytest
import globus_sdk

SKIP_INTEG = bool(os.getenv('SKIP_INTEGRATION_TESTS') != 'False')


@pytest.mark.skipif(SKIP_INTEG, reason='Integration test')
def test_refresh(live_client):
    live_client.logout()
    tokens = live_client.login(refresh_tokens=True)
    for tset in tokens.values():
        tset['expires_at_seconds'] = 0
    live_client.save_tokens([tokens])
    for rs, new_tokens in live_client.load_tokens().items():
        assert tokens[rs]['access_token'] != new_tokens['access_token']


@pytest.mark.skipif(SKIP_INTEG, reason='Integration test')
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


@pytest.mark.skip(SKIP_INTEG, reason='Integration test')
@pytest.mark.trylast
def test_refresh_no_longer_works_after_logout(live_client):
    tokens = live_client.login(refresh_tokens=True)
    live_client.logout()
    live_client.save_tokens(tokens)

    auth = live_client.get_authorizers()['auth.globus.org']
    auth.expires_at = 0
    with pytest.raises(globus_sdk.exc.AuthAPIError):
        auth.check_expiration_time()
