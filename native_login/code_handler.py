import os
import sys
import webbrowser
from contextlib import contextmanager
import six


class CodeHandler(object):
    """
    Generic handler for the code returned by the Native App Auth Flow in
    Globus Auth. It's intended to be subclassed to define the behavior for
    how the code gets from Globus Auth to the Native App.
    """

    def __init__(self, paste_url_in_browser_msg=None):
        self.paste_url_in_browser_msg = (
            paste_url_in_browser_msg or
            'Please paste the following URL in a browser: \n{}'
        )

    @contextmanager
    def start(self):
        """
        An extra method to do any extra startup before calling authenticate()
        For local_sever, this is a time to start a thread for a local TCP
        server for handling the auth code. For simple handlers like the
        InputCodeHandler, this can be safely ignored.
        """
        yield

    def get_redirect_uri(self):
        """
        For use with code handlers that don't know their redirect_uri until
        start() is called. For local_server, this is needed to find an open
        port number to return something like http://localhost:<PORT>/
        Return None to use the default Globus helper page
        """
        return None

    def set_app_name(self, app_name):
        """
        Optional method for setting the app name, if this is useful to the
        code handler. For local server, this is displayed on the local server's
        page.
        :param app_name: String to use for the app name.
        """
        pass

    def authenticate(self, url, no_browser=False):
        """
        Use the given url to direct the user to Globus Auth so they can login.
        :param url: URL to Globus Auth.
        :param no_browser: Don't automatically open the user's browser.
        :return:
        """
        if no_browser is False and not self.is_remote_session():
            webbrowser.open(url, new=1)
        else:
            self.write_message(self.paste_url_in_browser_msg)
        try:
            return self.get_code()
        except KeyboardInterrupt:
            self.write_message('Interrupt Received. '
                               'Canceling authentication...')
            sys.exit(-1)

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
        raise NotImplemented()

    def is_remote_session(self):
        """
        Check if this is being run from an ssh shell.
        :return: True if ssh shell, false otherwise
        """
        return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


class InputCodeHandler(CodeHandler):

    def get_code(self):
        self.write_message('Please Paste your Auth Code Below: ')
        return six.moves.input()
