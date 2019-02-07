import pytest
from native_login import NativeClient, ConfigParserTokenStorage


@pytest.fixture
def live_client():
    storage = ConfigParserTokenStorage(filename='integ_testing_tokens.cfg')
    client = NativeClient(client_id='7414f0b4-7d05-4bb6-bb00-076fa3f17cf5',
                          token_storage=storage,
                          default_scopes=['openid'])
    return client
