import pytest
from .mocks import MemoryStorage, MOCK_TOKEN_SET


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return MOCK_TOKEN_SET
