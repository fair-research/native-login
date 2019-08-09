import json
import os
import stat


class JSONTokenStorage(object):
    """
    Stores tokens in json format on disk in the local directory by default.
    """

    def __init__(self, filename=None, permission=None):
        self.filename = filename or 'mytokens.json'
        self.permission = permission or stat.S_IRUSR | stat.S_IWUSR

    def write_tokens(self, tokens):
        with open(self.filename, 'w+') as fh:
            json.dump(tokens, fh, indent=2)

    def read_tokens(self):
        if not os.path.exists(self.filename):
            return None
        with open(self.filename) as fh:
            content = fh.read()
            if content:
                return json.loads(content)

    def clear_tokens(self):
        os.remove(self.filename)
