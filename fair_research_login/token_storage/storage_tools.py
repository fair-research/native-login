from fair_research_login.exc import LoadError


def default_name_key(group_key, key, login):
    return 'login_{}__{}__{}'.format(login, group_key.replace('.', '_'), key)


def default_fetch_key(key):
    items = key.split('__')
    if len(items) == 2:
        return {'resource_server': items[0].replace('_', '.'),
                'token_name': items[1]}
    elif len(items) == 3:
        return {'login': int(items[0].replace('login_', '')),
                'resource_server': items[1].replace('_', '.'),
                'token_name': items[2]}
    else:
        raise LoadError('Failed to parse token key')


def flat_pack(token_list, name_key=default_name_key):
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
    for idx, tokens in enumerate(token_list):
        for token_set in tokens.values():
            for key, value in token_set.items():
                key_name = name_key(token_set['resource_server'], key,
                                    login=idx)
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
        return []

    login_groups = {}
    for fkey, fvalue in flat_tokens.items():
        key_data = fetch_key(fkey)
        login_no, resource_server, rs_key = (key_data.get('login', 0),
                                             key_data['resource_server'],
                                             key_data['token_name'])
        # Get the login info
        token_group = login_groups.get(login_no, {})
        # Get the resource server group
        resource_group = token_group.get(resource_server, {})
        resource_group[rs_key] = fvalue or None

        if rs_key == 'expires_at_seconds':
            exp = int(resource_group['expires_at_seconds'])
            resource_group['expires_at_seconds'] = exp

        token_group[resource_server] = resource_group
        login_groups[login_no] = token_group

    login_order = list(login_groups.keys())
    login_order.sort()
    sorted_token_list = []

    for tset_login_number in login_order:
        token_set = login_groups[tset_login_number]
        # It's possible for the 'fetch_key' to match the name of the resource
        # server. This shouldn't matter if we only rely on the key for fetching
        # items and use the stored value in 'resource_server' for the real name
        ts = {tset['resource_server']: tset for tset in token_set.values()}
        sorted_token_list.append(ts)
    return sorted_token_list
