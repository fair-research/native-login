import json
import os
from native_login.token_storage.token_storage import TokenStorage


class JSONTokenStorage(TokenStorage):

    def write_tokens(self, tokens):
        with open(self.filename, 'w+') as fh:
            json.dump(tokens, fh, indent=2)

    def read_tokens(self):
        if not os.path.exists(self.filename):
            return None
        with open(self.filename) as fh:
            return json.load(fh)

    def clear_tokens(self):
        os.remove(self.filename)
