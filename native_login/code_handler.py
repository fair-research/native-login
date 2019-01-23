import os
import webbrowser


class CodeHandler:

    def __init__(self):
        self.message = 'Please paste the following URL in a browser: \n{}'
        self.redirect_uri = 'https://auth.globus.org/v2/web/auth-code'

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
            print(self.message)
        return self.get_code()

    def write_message(self, message):
        """
        This will likely be the only place where output needs to be directly
        written to the user. Some CLIs like click may prefer click.echo here
        rather than print.
        :param message: Direct Standard Output message for user consumption
        """
        print(message)

    def get_code(self):
        raise NotImplemented()

    def is_remote_session(self):
        return os.environ.get('SSH_TTY', os.environ.get('SSH_CONNECTION'))


class InputCodeHandler(CodeHandler):

    def get_code(self):
        return input()


class LocalServerHandler(CodeHandler):

    def __init__(self):
        super(LocalServerHandler, self).__init__()
        self.redirect_uri = 'https://auth.globus.org/v2/web/auth-code'
