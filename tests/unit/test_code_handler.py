import pytest
import sys

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock

from native_login.code_handler import CodeHandler


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
