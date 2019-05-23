from fair_research_login.exc import TokensExpired


def test_tokens_expired_str_contains_scopes():
    scopes = ['foo', 'bar', 'baz']
    te = TokensExpired('oh noes!', scopes=scopes)
    assert all([s in str(te) for s in scopes])
