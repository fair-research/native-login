import pytest
from copy import deepcopy
from .mocks import MemoryStorage, MOCK_TOKEN_SET


@pytest.fixture
def mem_storage():
    return MemoryStorage()


@pytest.fixture
def mock_tokens():
    return deepcopy(MOCK_TOKEN_SET)
