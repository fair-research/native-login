from uuid import uuid4
from native_login.client import NativeClient
from native_login.token_storage.configparser_token_storage import (
    MultiClientTokenStorage
)
from native_login.local_server import LocalServerCodeHandler


def test_client_defaults():
    cli = NativeClient(client_id=str(uuid4()))
    assert isinstance(cli.token_storage, MultiClientTokenStorage)
    assert isinstance(cli.local_server, LocalServerCodeHandler)
