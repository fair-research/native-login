import json
import os


class JSONTokenStorage(object):
    """
    Stores tokens in json format on disk in the local directory by default.
    """

    def __init__(self, filename=None):
        self.filename = filename or 'mytokens.json'

    def write_tokens(self, tokens):
        with open(self.filename, 'w+') as fh:
            json.dump(tokens.by_resource_server, fh, indent=2)

    def read_tokens(self):
        if not os.path.exists(self.filename):
            return None
        with open(self.filename) as fh:
            return json.load(fh)

    def clear_tokens(self):
        os.remove(self.filename)
