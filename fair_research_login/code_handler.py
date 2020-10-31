import os
import logging
import webbrowser
from contextlib import contextmanager
import six

log = logging.getLogger(__name__)


class CodeHandler(object):
    """
    Generic handler for the code returned by the Native App Auth Flow in
    Globus Auth. It's intended to be subclassed to define the behavior for
    how the code gets from Globus Auth to the Native App.
    """
    _browser_enabled = True

    def __init__(self, paste_url_in_browser_msg=None):
        self.client = None
        self.app_name = ''
        self.no_browser = False
        self.paste_url_in_browser_msg = (
            paste_url_in_browser_msg or
            'Please paste the following URL in a browser'
        )

    @staticmethod
    def is_browser_enabled():
        """
        Will login automatically open the users browser to the Globus Auth
        Link? If False, the user will need to manually open a browser and
        copy/paste the link.
        """
        return CodeHandler._browser_enabled

    @staticmethod
    def set_browser_enabled(value):
        """
        Set whether login will automatically open the users browser to the
        Globus Auth Link. GLOBAL SETTING, this will affect ALL Code Handlers.
        """
        if value not in (True, False):
            raise ValueError('Value must be True or False')
        log.info('Global setting for automatic browser set: {}'.format(value))
        CodeHandler._browser_enabled = value

    @contextmanager
    def start(self):
        """
        An extra method to do any extra startup before calling authenticate()
        For local_sever, this is a time to start a thread for a local TCP
        server for handling the auth code. For simple handlers like the
        InputCodeHandler, this can be safely ignored.
        """
        yield

    def is_available(self):
        """
        Can this code handler be used? If False, the client will skip this
        handler and use the next one in the list. Typically this will be
        used for the LocalServerCodeHandler when in an SSH session so it
        can abort and use a InputCodeHandler instead.
        """
        return True

    def is_browser_available(self):
        is_rem, is_enb = self.is_remote_session(), self.is_browser_enabled()
        available = is_rem is False and is_enb is True
        log.debug('Browser| Remote: {}, Enabled: {}, Available: {}'
                  ''.format(is_rem, is_enb, available))
        return available

    def get_redirect_uri(self):
        """
        For use with code handlers that don't know their redirect_uri until
        start() is called. For local_server, this is needed to find an open
        port number to return something like http://localhost:<PORT>/
        Return None to use the default Globus helper page
        """
        return None

    def set_context(self, client, **kwargs):
        """
        Set context for a given code handler, which includes the NativeClient
        itself and any login_kwargs.
        """
        self.client = client
        self.app_name = client.app_name
        self.no_browser = kwargs.get('no_browser') or self.no_browser

    def authenticate(self, url):
        """
        Use the given url to direct the user to Globus Auth so they can login.
        :param url: URL to Globus Auth.
        :return:
        """
        open_browser = self.no_browser is False
        if self.is_browser_available() and open_browser:
            webbrowser.open(url, new=1)
        else:
            self.write_message('{}:\n{}'.format(self.paste_url_in_browser_msg,
                                                url))
        try:
            return self.get_code()
        except KeyboardInterrupt:
            log.info('Disabling browser due to user keyboard interrupt.')
            self.set_browser_enabled(False)
            raise

    def write_message(self, message):
        """
        This will likely be the only place where output needs to be directly
        written to the user. Some CLIs like Click may prefer click.echo here
        rather than print.
        :param message: Direct Standard Output message for user consumption
        """
        print(message)

    def get_code(self):
        """
        Override in child. Get the code returned by Globus Auth to complete
        the Native App Auth Flow.
        :return: Code returned by Globus Auth
        """
        raise NotImplementedError()

    def is_remote_session(self):
        """
        Check if this is being run from an ssh shell.
        :return: True if ssh shell, false otherwise
        """
        return bool(os.environ.get('SSH_TTY') or
                    os.environ.get('SSH_CONNECTION'))


class InputCodeHandler(CodeHandler):

    def get_code(self):
        self.write_message('Please Paste your Auth Code Below: ')
        return six.moves.input()
