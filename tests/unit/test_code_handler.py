import pytest

from fair_research_login.code_handler import InputCodeHandler, CodeHandler


def test_code_handler_extendable_methods():
    with pytest.raises(Exception):
        CodeHandler().get_code()


def test_code_handler_authenticate_with_webbrowser(mock_webbrowser,
                                                   mock_input,
                                                   mock_is_remote_session):
    CodeHandler.set_browser_enabled(True)
    InputCodeHandler().authenticate('http://foo.edu')
    assert mock_input.called
    assert mock_webbrowser.called


def test_code_handler_set_browser_enabled_is_boolean():
    with pytest.raises(ValueError):
        CodeHandler.set_browser_enabled('invalid value')


def test_code_handler_authenticate_without_webbrowser(mock_webbrowser,
                                                      mock_input):
    CodeHandler.set_browser_enabled(False)
    InputCodeHandler().authenticate('http://foo.edu')
    assert mock_input.called
    assert not mock_webbrowser.called
    CodeHandler.set_browser_enabled(True)


def test_code_handler_authenticate_with_ssh_session(mock_webbrowser,
                                                    mock_input,
                                                    monkeypatch):
    CodeHandler.set_browser_enabled(True)
    monkeypatch.setenv('SSH_TTY', 'SSH_CONNECTION')
    InputCodeHandler().authenticate('http://foo.edu')
    assert mock_input.called
    assert not mock_webbrowser.called
