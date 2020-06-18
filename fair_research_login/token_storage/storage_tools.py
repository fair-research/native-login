import time
import copy
import sys

from fair_research_login.exc import (TokensExpired, ScopesMismatch,
                                     InvalidTokenFormat)

string_types = str if sys.version_info.major == 3 else basestring  # noqa

TOKEN_GROUP_KEYS = {'access_token', 'refresh_token', 'expires_at_seconds',
                    'scope', 'token_type', 'resource_server'}
REQUIRED_TOKEN_KEYS = {'access_token', 'expires_at_seconds', 'scope',
                       'resource_server'}


def is_expired(token_set):
    return time.time() >= token_set['expires_at_seconds']


def check_expired(tokens):
    """
    Returns a Token Group organized by:
    globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
    For all tokens in that group that are expired. Ignores whether there
    is a refresh token attached to that token.
    """
    expired = [rs for rs, tset in tokens.items() if is_expired(tset)]
    if expired:
        raise TokensExpired(resource_servers=expired)


def get_scopes(tokens):
    """Fetch scopes for tokens given a dict of tokens grouped by resource
    server. """
    scopes = [tset['scope'].split() for tset in tokens.values()]
    # Get flattened list of scopes
    return [item for sublist in scopes for item in sublist]


def check_scopes(tokens, requested_scopes):
    """
    Returns true if scopes match the tokens passed in, false otherwise.
    **Parameters**
      ``tokens`` (**dict**)
      A token grouping, organized by:
      globus_sdk.auth.token_response.OAuthTokenResponse.by_resource_server
      Example:
        {
            'auth.globus.org': {
                'scope': 'openid profile email',
                'access_token': '<token>',
                'refresh_token': None,
                'token_type': 'Bearer',
                'expires_at_seconds': 1234567,
                'resource_server': 'auth.globus.org'
            }, ...
        }
    """
    loaded_scopes = get_scopes(tokens)
    diff = set(requested_scopes).difference(set(loaded_scopes))
    if diff:
        raise ScopesMismatch('Loaded Scopes missing Requested Scopes {}'
                             ''.format(diff))


def verify_token_group(tokens):
    """Verifies a token group is a valid dict with valid values. Does NOT check
    whether the token has expired or if the token(s) are invalid. Validation
    is not absolutely strict and allows some deviance for values, for example
    'refresh_token' may be any falsy value. If validation passes, a cleaned
     dict is returned with the following values:

    * access_token: A string
    * refresh_token: A valid string or None
    * scope: A string
    * expires_at_seconds: An integer
    * token_type: 'Bearer'

    The following validation asserts the following:

    * tokens is a dict
    * tokens contains no more than the following:
     {'access_token', 'refresh_token', 'expires_at_seconds',
     'scope', 'token_type', 'resource_server'}
    * The token group contains no less than the following:
     {'access_token', 'expires_at_seconds', 'scope', 'resource_server'}
    * 'access_token' and 'scope' must be strings
    * 'token_type' is 'Bearer' if it is present
    * 'refresh_token' must be falsy or a string.
    * 'expires_at_seconds' must be an integer or parsable integer
        * valid examples include: 123, '123', 123.456
        * invalid examples include: 'abc', '123abc'

    """
    cleaned = copy.deepcopy(tokens)

    if not isinstance(tokens, dict):
        raise InvalidTokenFormat('Tokens must be a dict.', code='not_dict')
    tk_set = set(tokens.keys())

    if not tk_set.issubset(TOKEN_GROUP_KEYS):
        raise InvalidTokenFormat('Received unexpected values: {}'.format(
            tk_set.difference(TOKEN_GROUP_KEYS)), code='unexpected_values')

    if not tk_set.issuperset(REQUIRED_TOKEN_KEYS):
        raise InvalidTokenFormat('Missing required values: {}'.format(
            REQUIRED_TOKEN_KEYS.difference(tk_set)), code='missing_required')

    for tp in ['access_token', 'scope', 'resource_server']:
        if not isinstance(tokens.get(tp, ''), string_types):
            raise InvalidTokenFormat('{} must be a string.'.format(tp),
                                     code='invalid_type')
        cleaned[tp] = tokens[tp]

    if tokens.get('token_type') and tokens['token_type'] != 'Bearer':
        raise InvalidTokenFormat('token_type must be "Bearer"',
                                 code='invalid_token_type')
    cleaned['token_type'] = 'Bearer'

    rt = tokens.get('refresh_token')
    if rt and not isinstance(rt, string_types):
        raise InvalidTokenFormat('refresh_token must be a str or falsy',
                                 code='invalid_type')
    cleaned['refresh_token'] = rt or None

    try:
        cleaned['expires_at_seconds'] = int(tokens['expires_at_seconds'])
    except ValueError:
        raise InvalidTokenFormat('expires_at_seconds must be an integer',
                                 code='invalid_type')
    return cleaned


def default_name_key(group_key, key):
    return '{}__{}'.format(group_key.replace('.', '_'), key)


def default_fetch_key(key):
    resource_server, token_name = key.split('__')
    return resource_server.replace('_', '.'), token_name


def flat_pack(tokens, name_key=default_name_key):
    """
    Take a dict of tokens organized by resource server and return a dict
    that can be easily saved to a config file.
    Resource servers containing '.' in their name will automatically be
    converted to '_' (auth.globus.org == auth_globus_org). Tokens by default
    are prefixed by this name, which you can modify with by setting the
    name_item() function. An example is here:

    name_item = lambda key, token: '{}_{}'.format(key.replace('.', '_'), token)

    which results in a token name being written as:

    auth_globus_org_access_token = <value>

    Int values are converted to string, None values are converted
    to empty string. *No other types are checked*.
    `tokens` should be formatted:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    Returns a flat dict of tokens prefixed by resource server.
    {
        "auth_globus_org_scope": "profile openid email",
        "auth_globus_org_access_token": "<token>",
        "auth_globus_org_refresh_token": "",
        "auth_globus_org_token_type": "Bearer",
        "auth_globus_org_expires_at_seconds": "1540051101",
        "auth_globus_org_resource_server": "auth.globus.org",
        "token_groups": "auth_globus_org"
    }"""

    flattened_items = {}
    for token_set in tokens.values():
        for key, value in token_set.items():
            key_name = name_key(token_set['resource_server'], key)
            if isinstance(value, int):
                value = str(value)
            if value is None:
                value = ""
            flattened_items[key_name] = value

    return flattened_items


def flat_unpack(flat_tokens, fetch_key=default_fetch_key):
    """
    Takes a dict from a config section and returns a dict of tokens by
    resource server. `config_items` is a raw dict of config options
    returned from get_parser().get_section().
    Returns tokens in the format:
    {
        "auth.globus.org": {
            "scope": "profile openid email",
            "access_token": "<token>",
            "refresh_token": None,
            "token_type": "Bearer",
            "expires_at_seconds": 1539984535,
            "resource_server": "auth.globus.org"
        }, ...
    }
    """
    if not flat_tokens:
        return {}

    token_sets = {}
    for fkey, fvalue in flat_tokens.items():
        resource_server, key = fetch_key(fkey)
        tset = token_sets.get(resource_server, {})
        tset[key] = fvalue or None

        if key == 'expires_at_seconds':
            tset['expires_at_seconds'] = int(tset['expires_at_seconds'])

        token_sets[resource_server] = tset
    # It's possible for the 'fetch_key' to match the name of the resource
    # server. This shouldn't matter if we only rely on the key for fetching
    # items and use the stored value in 'resource_server' for the real name
    return {tset['resource_server']: tset for tset in token_sets.values()}
