import threading
import requests

import pytest
from six.moves.urllib.parse import urlencode

from fair_research_login.local_server import LocalServerCodeHandler
from fair_research_login.exc import LocalServerError


class LocalServerTester:
    def __init__(self, handler):
        self.handler = handler
        self.server_response = None
        self.response = None

    def _wait_for_code(self):
        try:
            self.server_response = self.handler.get_code()
        except Exception as e:
            self.server_response = e

    def test(self, response_params):
        """
        Start a local server to wait for an 'auth_code'. Usually the user's
        browser will redirect to this location, but in this case the user is
        mocked with a separate request in another thread.
        Waits for threads to complete and returns the local_server response.
        """
        with self.handler.start():
            thread = threading.Thread(target=self._wait_for_code)
            thread.start()
            url = "{}/?{}".format(self.handler.get_redirect_uri(),
                                  urlencode(response_params))
            self.response = requests.get(url)
            thread.join()
            return self.server_response


def test_local_server_with_auth_code():
    server = LocalServerTester(LocalServerCodeHandler())
    assert server.test({"code": 'test_code'}) == 'test_code'


def test_local_server_with_error():
    server = LocalServerTester(LocalServerCodeHandler())
    response = server.test({"error": "bad things happened"})
    assert isinstance(response, LocalServerError)


def test_local_server_with_custom_template():
    template = 'HIGHLY CUSTOMIZED TEMPLATE'

    server = LocalServerTester(LocalServerCodeHandler(template=template))
    server.test({'code': 'test_code'})
    assert server.response.text == template

    # Test you don't need to pass $error in the template
    server = LocalServerTester(LocalServerCodeHandler(template=template))
    server.test({'error': 'a bad thing'})
    assert server.response.text == template


def test_local_server_with_custom_template_vars():
    template_vars = {
        'defaults': {
            'app_name': '',  # Auto-populated if blank, but can be changed
            'post_login_message': 'you are now logged in, congrats!',
            'error': '',  # Present if there is an error in Globus Auth
            'login_result': ''
        },
        'error': {},
        'success': {}
    }

    class MockNativeClient:
        app_name = 'My Wicked Cool App'

    local_server = LocalServerCodeHandler(template_vars=template_vars)
    local_server.set_context(MockNativeClient)
    server = LocalServerTester(local_server)
    server.test({'code': 'test_code'})
    assert (template_vars['defaults']['post_login_message'] in
            server.response.text)
    assert 'My Wicked Cool App' in server.response.text


def test_bad_template_vars():
    tvars = {'defaults': {}}
    with pytest.raises(ValueError):
        server = LocalServerTester(LocalServerCodeHandler(template_vars=tvars))
        server.test({'code': 'test_code'})


def test_missing_template_vars():
    tvars = {'defaults': {'foo': 'bar'}, 'error': {}, 'success': {}}
    with pytest.raises(KeyError):
        server = LocalServerTester(LocalServerCodeHandler(template_vars=tvars))
        server.test({'code': 'test_code'})


def test_access_server_before_started():
    with pytest.raises(LocalServerError):
        LocalServerCodeHandler().server


def test_server_timeout():
    handler = LocalServerCodeHandler()
    with handler.start():
        handler.server.timeout = 1
        with pytest.raises(LocalServerError):
            handler.get_code()
