import json
from native_login.token_handlers.base import TokenHandler


class JSONTokenHandler(TokenHandler):

    def write(self, tokens):
        with open(self.filename, 'w+') as fh:
            json.dump(tokens, fh, indent=2)

    def read(self):
        with open(self.filename) as fh:
            return json.load(fh)
