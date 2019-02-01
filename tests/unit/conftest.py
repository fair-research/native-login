import pytest
import webbrowser
from copy import deepcopy
from .mocks import MemoryStorage, MOCK_TOKEN_SET
from native_login import NativeClient
import six

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return deepcopy(MOCK_TOKEN_SET)


@pytest.fixture
def mock_input(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(six.moves, 'input', mock)
    return mock


@pytest.fixture
def mock_webbrowser(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(webbrowser, 'open', mock)
    return mock


@pytest.fixture
def mock_revoke(monkeypatch):
    mock = Mock()
    monkeypatch.setattr(NativeClient, 'oauth2_revoke_token', mock)
    return mock
