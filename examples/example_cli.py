"""
If you're building your own resource server, or have a complex task you want
to do often, you may want your own command line client similar to Globus-Cli.

This can be run in two ways, the first simply on command line:
    python example_cli.py

Or, if you want other people to be able to install your package and write
their own scripts by calling into your tool, you can import it instead

    from example_cli import cli
    cli.login()
    cli.say_hello()
    cli.logout()
"""

from argparse import ArgumentParser
from globus_sdk import AuthClient
from native_login import NativeClient, ConfigParserTokenStorage, LoadError

parser = ArgumentParser(prog='Example Client')
subparsers = parser.add_subparsers(dest='subcommand')

login = subparsers.add_parser('login', help='Login to My Client')
login.add_argument('--no-local-server', action='store_true')
login.add_argument('--no-browser', action='store_true')
login.add_argument('--remember-me', action='store_true')

logout = subparsers.add_parser('logout', help='Revoke and clear tokens')

hello = subparsers.add_parser('hello', help='A friendly welcome')


class MyClient(NativeClient):

    def __init__(self):
        client_id = '7414f0b4-7d05-4bb6-bb00-076fa3f17cf5'
        storage = ConfigParserTokenStorage(filename='config.cfg',
                                           section='tokens')
        # You can provide `default_scopes` for the scopes you need for your
        # client to run. This is especially handy if you have defined a custom
        # scope for your app's resource server.
        super(MyClient, self).__init__(client_id=client_id,
                                       token_storage=storage,
                                       default_scopes=['profile', 'openid'])

    def say_hello(self):
        # Loads RefreshTokenAuthorizer if login(refresh_tokens=True), otherwise
        # will load an AccessTokenAuthorizer
        ac_authorizer = self.get_authorizers()['auth.globus.org']
        auth_cli = AuthClient(authorizer=ac_authorizer)
        user_info = auth_cli.oauth2_userinfo()
        print('Hello {}! How are you today?'.format(user_info['name']))

    def is_logged_in(self):
        try:
            self.load_tokens()
            return True
        except LoadError:
            return False


cli = MyClient()

if __name__ == '__main__':
    # parse some argument lists
    args = parser.parse_args()
    if args.subcommand == 'login':
        if cli.is_logged_in():
            print('You are already logged in')
        else:
            cli.login(no_local_server=args.no_local_server,
                      no_browser=args.no_browser,
                      refresh_tokens=args.remember_me)
            print('Login Successful')

    if args.subcommand == 'logout':
        cli.logout()
        print('You have been logged out.')

    if args.subcommand == 'hello':
        if cli.is_logged_in():
            cli.say_hello()
        else:
            print('Who are you again? Login so I can get your name.')

    if args.subcommand is None:
        parser.print_help()
