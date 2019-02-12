import pytest
import sys

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from fair_research_login.code_handler import InputCodeHandler, CodeHandler


def test_code_handler_extendable_methods():
    with pytest.raises(Exception):
        CodeHandler().get_code()


def test_code_handler_exits_on_interrupt(monkeypatch):

    monkeypatch.setattr(sys, 'exit', Mock())

    class MyCodeHandler(CodeHandler):
        def get_code(self):
            raise KeyboardInterrupt()

    MyCodeHandler().authenticate('foo', no_browser=True)
    assert sys.exit.called


def test_code_handler_authenticate_with_webbrowser(mock_webbrowser,
                                                   mock_input):
    InputCodeHandler().authenticate('http://foo.edu', no_browser=False)
    assert mock_input.called
    assert mock_webbrowser.called


def test_code_handler_authenticate_without_webbrowser(mock_webbrowser,
                                                      mock_input):
    InputCodeHandler().authenticate('http://foo.edu', no_browser=True)
    assert mock_input.called
    assert not mock_webbrowser.called


def test_code_handler_authenticate_with_ssh_session(mock_webbrowser,
                                                    mock_input,
                                                    monkeypatch):
    monkeypatch.setenv('SSH_TTY', 'SSH_CONNECTION')
    InputCodeHandler().authenticate('http://foo.edu', no_browser=False)
    assert mock_input.called
    assert not mock_webbrowser.called
