import logging
import threading
from contextlib import contextmanager
import string
import queue
from urllib.parse import parse_qsl, urlparse, urlunparse

try:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
except ImportError:
    from http.server import HTTPServer, BaseHTTPRequestHandler

from fair_research_login.exc import LocalServerError
from fair_research_login.code_handler import CodeHandler

log = logging.getLogger(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en-US">
<head>
  <meta charset="utf-8">
  <meta http-equiv="x-ua-compatible" content="ie=edge">
  <title>$app_name Login</title>
  <style type="text/css" media="screen">
    html { font: 75% "Helvetica Neue","Arial","Helvetica",sans-serif }
    html, body { display: block; margin: 0; padding: 0 }
    a { color: #5783a6; text-decoration: none; }
    a img { border: none; }
    header { background: #2e5793; }
    main { padding: 25px 0 50px; }
    main h1 { border-bottom: solid 1px #aaa; font-size: 233.33%;
              font-weight: normal; }
    main img { display: block; margin: 0 auto; max-width: 100%; height: auto; }
    main p { color: #333; font-size: 116.67%; max-width: 560px;
             margin: 1em auto; line-height: 150%; }
    header > div, main, footer { display: block; max-width: 980px;
                                 margin: 0 auto; }
  </style>
</head>
<body>
  <header><div><a href="https://www.globus.org" title="Go to Globus.org Home">
    <img alt="Globus" width="215" height="64"
         src="data:image/png;base64,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">
  </a></div></header>

  <main>
    <h1>$app_name</h1>
    <p>
      $login_result. You may close this tab.
    </p>
    <p>
      $error
    </p>
    <p>
      $post_login_message
    </p>
  </main>
</body>
</html>
"""

DEFAULT_VARS = {
    'defaults': {
        'app_name': '',
        'login_result': '',
        'post_login_message': '',
        'error': '',
    },
    'success': {
        'login_result': 'Login Successful',
    },
    'error': {
        'login_result': 'Login Failed',
    }
}


class LocalServerCodeHandler(CodeHandler):

    def __init__(self, template=None, template_vars=None,
                 hostname='localhost', cli_message=None):
        super(LocalServerCodeHandler, self).__init__()
        self._server = None
        self.hostname = hostname
        self.template = string.Template(template or HTML_TEMPLATE)
        self.template_vars = template_vars or DEFAULT_VARS
        default_message = ('Starting login with Globus Auth, '
                           'press ^C to cancel.')
        self.cli_message = cli_message or default_message
        self.no_local_server = False

    def is_available(self):
        local = self.is_remote_session() is False
        enabled = self.no_local_server is False
        log.debug('Local Server: Local: {} Enabled: {}'.format(local, enabled))
        return local and enabled

    def set_context(self, *args, **kwargs):
        super(LocalServerCodeHandler, self).set_context(*args, **kwargs)
        if not self.template_vars.get('defaults', {}).get('app_name'):
            self.template_vars['defaults']['app_name'] = self.app_name
        self.no_local_server = (kwargs.get('no_local_server') or
                                self.no_local_server)

    @property
    def server(self):
        if self._server is None:
            raise LocalServerError('server referenced before start() called!')
        else:
            return self._server

    @contextmanager
    def start(self):
        self._server = RedirectHTTPServer(self.template, self.template_vars)
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()
        self.write_message(self.cli_message)

        yield

        self._server.shutdown()
        del self._server

    def get_redirect_uri(self):
        _, port = self.server.server_address
        host = '{}:{}'.format(self.hostname, port)
        return urlunparse(('http', host, '', None, None, None))

    def get_code(self):
        return self.server.wait_for_code()


class RedirectHandler(BaseHTTPRequestHandler):

    def do_GET(self):  # noqa
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        query_params = dict(parse_qsl(urlparse(self.path).query))
        code = query_params.get('code')
        error = query_params.get('error_description',
                                 query_params.get('error'))

        resp = self.server.success() if code else self.server.error()
        self.wfile.write(resp)
        self.server.return_code(code or LocalServerError(error))

    def log_message(self, format, *args):
        return


class RedirectHTTPServer(HTTPServer, object):

    DEFAULT_LISTEN = ('0.0.0.0', 0)
    DEFAULT_HANDLER = RedirectHandler
    VARS_KEYS = {'success', 'error'}

    def __init__(self, template, vars, listen=None, handler_class=None,
                 timeout=3600):
        HTTPServer.__init__(
            self,
            listen or RedirectHTTPServer.DEFAULT_LISTEN,
            handler_class or RedirectHTTPServer.DEFAULT_HANDLER
        )
        self._auth_code_queue = queue.Queue()
        self.template = template
        self.vars = vars
        self.timeout = timeout
        if not self.VARS_KEYS.issubset(set(vars.keys())):
            raise ValueError('Vars must contain two dicts: {}'
                             ''.format(self.VARS_KEYS))
        for key in self.VARS_KEYS:
            self.template_test(key)

    def template_test(self, key):
        try:
            self.render_template(key)
        except KeyError as ke:
            raise KeyError('"{}" template var "{}" was not provided'
                           ''.format(key, ','.join(ke.args)))

    def success(self):
        return self.render_template('success')

    def error(self):
        return self.render_template('error')

    def render_template(self, key):
        tvars = self.vars.get('defaults', {})
        tvars.update(self.vars[key])
        return bytes(self.template.substitute(tvars), 'utf-8')

    def return_code(self, code):
        self._auth_code_queue.put_nowait(code)

    def wait_for_code(self):
        # workaround for handling control-c interrupt.
        # relevant Python issue discussing this behavior:
        # https://bugs.python.org/issue1360
        try:
            resp = self._auth_code_queue.get(block=True, timeout=self.timeout)
            if isinstance(resp, LocalServerError):
                raise resp
            return resp
        except queue.Empty:
            raise LocalServerError()
        finally:
            # shutdown() stops the server thread
            # https://github.com/python/cpython/blob/3.7/Lib/socketserver.py#L241
            self.shutdown()
            # server_close() closes the socket:
            # https://github.com/python/cpython/blob/3.7/Lib/socketserver.py#L474
            self.server_close()
