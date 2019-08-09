
"""
The most basic usage automatically saves and loads tokens, and provides
a local server for logging in users.
"""
import os
import pytest
import globus_sdk
import fair_research_login

# Set integration tests by running `export RUN_INTEGRATION_TESTS=True`
RUN_INTEGRATION_TESTS = os.getenv('RUN_INTEGRATION_TESTS') == 'True'


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason='Integration test')
def test_refresh(live_client):
    tokens = live_client.login(refresh_tokens=True)
    for tset in tokens.values():
        tset['expires_at_seconds'] = 0
        tset['access_token'] = 'foo'
    live_client.save_tokens(tokens)
    for rs, new_tokens in live_client.load_tokens().items():
        assert tokens[rs]['access_token'] != new_tokens['access_token']


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason='Integration test')
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


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason='Integration test')
def test_refresh_no_longer_works_after_logout(live_client_destructive):
    tokens = live_client_destructive.login(refresh_tokens=True)
    live_client_destructive.logout()
    live_client_destructive.save_tokens(tokens)

    auth = live_client_destructive.get_authorizers()['auth.globus.org']
    auth.expires_at = 0
    with pytest.raises(globus_sdk.exc.AuthAPIError):
        auth.check_expiration_time()


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason='Integration test')
def test_load_live_token_when_another_inactive(live_client_destructive):
    tokens = live_client_destructive.login()
    tokens['auth.globus.org']['expires_at_seconds'] = 0
    tokens['auth.globus.org']['access_token'] = 'fooey!'

    live_client_destructive.save_tokens(tokens)
    new_scope = ['urn:globus:auth:scope:transfer.api.globus.org:all']
    live_client_destructive.login(requested_scopes=new_scope)

    assert len(live_client_destructive.load_tokens().keys()) == 1
    tk = live_client_destructive.load_tokens(requested_scopes=new_scope).keys()
    assert len(tk) == 1


@pytest.mark.skipif(not RUN_INTEGRATION_TESTS, reason='Integration test')
def test_load_refresh_tokens_catches_refresh_error(live_client_destructive):
    tokens = live_client_destructive.login(refresh_tokens=True)
    live_client_destructive.revoke_token_set(tokens)
    tokens['auth.globus.org']['expires_at_seconds'] = 0
    live_client_destructive.save_tokens(tokens)

    # Should not raise sdk exception due to invalid grant:
    # globus_sdk.exc.AuthAPIError: (400, 'Error', 'invalid_grant')
    with pytest.raises(fair_research_login.LoadError):
        live_client_destructive.load_tokens()
