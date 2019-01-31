import os
from six.moves.configparser import ConfigParser, NoSectionError

from native_login.token_storage.token_storage import TokenStorage
from native_login.token_storage.storage_tools import flat_pack, flat_unpack


class ConfigParserTokenStorage(TokenStorage):

    CONFIG_TOKEN_GROUPS = "token_groups"
    CFG_SECTION = 'tokens'

    def __init__(self, filename=None, section=None):
        super(ConfigParserTokenStorage, self).__init__(filename=filename)
        self.section = section or self.CFG_SECTION

    def read_config_parser(self):
        config = ConfigParser()
        config.read(self.filename)
        if self.section not in config.sections():
            config.add_section(self.section)
        return config

    def write_config_parser(self, config):
        with open(self.filename, 'w') as configfile:
            config.write(configfile)

    def write_tokens(self, tokens):
        config = self.read_config_parser()
        for name, value in tokens.items():
            config.set(self.section, name, value)
        self.write_config_parser(config)

    def read_tokens(self):
        config = self.read_config_parser()
        return dict(config.items(self.section))

    def clear_tokens(self):
        os.remove(self.filename)

    def serialize_tokens(self, oauth2_token_response):
        return flat_pack(oauth2_token_response.by_resource_server)

    def deserialize_tokens(self, packed_tokens):
        return flat_unpack(packed_tokens)


class MultiClientTokenStorage(ConfigParserTokenStorage):

    def set_client_id(self, client_id):
        self.section = client_id

    def clear(self):
        config = self.read_config_parser()
        if self.section in config.sections():
            config.remove_section(self.section)
            self.write_config_parser(config)
