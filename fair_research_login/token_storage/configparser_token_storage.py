import os
import stat
from six.moves.configparser import ConfigParser

from fair_research_login.token_storage.storage_tools import (
    flat_pack, flat_unpack
)


class ConfigParserTokenStorage(object):
    """
    Basic ConfigParser object for both python 2 and 3. This object provides the
    basics for token storage, and basic save/load functions for writing/reading
    config data to disk.
    """
    DEFAULT_FILENAME = os.path.expanduser('~/.globus-native-apps.cfg')
    DEFAULT_PERMISSION = stat.S_IRUSR | stat.S_IWUSR
    CONFIG_TOKEN_GROUPS = 'token_groups'
    CFG_SECTION = 'tokens'

    def __init__(self, filename=None, section=None, permission=None):
        self.section = section or self.CFG_SECTION
        self.filename = filename or self.DEFAULT_FILENAME
        self.permission = permission or self.DEFAULT_PERMISSION

    def load(self):
        config = ConfigParser()
        config.read(self.filename)
        if self.section not in config.sections():
            config.add_section(self.section)
        return config

    def save(self, config):
        with open(self.filename, 'w') as configfile:
            config.write(configfile)
        os.chmod(self.filename, self.DEFAULT_PERMISSION)

    def write_tokens(self, tokens):
        config = self.load()
        for name, value in flat_pack(tokens).items():
            config.set(self.section, name, value)
        self.save(config)

    def read_tokens(self):
        return flat_unpack(dict(self.load().items(self.section)))

    def clear_tokens(self):
        config = self.load()
        config.remove_section(self.section)
        config.add_section(self.section)
        self.save(config)


class MultiClientTokenStorage(ConfigParserTokenStorage):
    """
    A very specific implementation for NativeClient, and serves as a nice
    default for saving tokens for multiple Globus Apps, storing each app's
    tokens in a separate section by client_id.
    """

    def set_client_id(self, client_id):
        self.section = client_id
