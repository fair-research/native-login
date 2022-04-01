import uuid
import os
import sys

import pytest

from unittest.mock import Mock, mock_open, patch
from fair_research_login import (ConfigParserTokenStorage, JSONTokenStorage,
                                 NativeClient)
from .mocks import MOCK_TOKEN_SET, CONFIGPARSER_VALID_CFG


def test_json_token_storage(mock_tokens, mock_revoke, monkeypatch):
    cli = NativeClient(client_id=str(uuid.uuid4()),
                       token_storage=JSONTokenStorage())
    # Mock actual call to open(). Catch the data 'written' and use it in the
    # load function. This is a cheap and easy (and hacky) way to test that the
    # stuff we get read was the same as the stuff written in.
    monkeypatch.setattr(os.path, 'exists', lambda x: True)
    mo = mock_open()
    with patch('builtins.open', mo):
        from pprint import pprint
        pprint(mock_tokens)
        cli.save_tokens(mock_tokens)
        written = ''.join([c[1][0] for c in mo().write.mock_calls])
    with patch('builtins.open', mock_open(read_data=written)):
        tokens = cli.load_tokens()
        assert tokens == MOCK_TOKEN_SET
        mock_remove = Mock()
        with patch('os.remove', mock_remove):
            cli.logout()
            assert mock_remove.called


def test_json_token_storage_non_existant_filename():
    store = JSONTokenStorage(filename=str(uuid.uuid4()))
    assert store.read_tokens() is None


def test_config_parser_read_token_storage(mock_token_response):
    cfg = ConfigParserTokenStorage(filename=CONFIGPARSER_VALID_CFG)
    tokens = cfg.read_tokens()
    assert isinstance(tokens, dict)
    assert tokens.get('resource.server.org')
    assert len(tokens['resource.server.org'].values()) == 6


def test_config_parser_write_token_storage(mock_tokens):
    cfg = ConfigParserTokenStorage(filename=CONFIGPARSER_VALID_CFG)
    mo = mock_open()
    with patch('builtins.open', mo):
        cfg.write_tokens(mock_tokens)
        written = ''.join([c[1][0] for c in mo().write.mock_calls])

    token_data = mock_tokens['resource.server.org']
    del token_data['refresh_token']
    for val in token_data.values():
        assert str(val) in written


def test_config_parser_clear_token_storage(monkeypatch):
    cfg = ConfigParserTokenStorage(filename=CONFIGPARSER_VALID_CFG,
                                   section='tokens')
    mock_save = Mock()
    monkeypatch.setattr(cfg, 'save', mock_save)
    cfg.clear_tokens()
    assert mock_save.called
    assert mock_save.call_args[0][0].items('tokens') == []
