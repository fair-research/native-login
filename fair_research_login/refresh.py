

class RefreshHelper(object):

    def __init__(self, native_client_instance, scope_set):
        self.nc_instance = native_client_instance
        self.scope_set = scope_set

    def __call__(self, token_response):
        login_groups = self.nc_instance._load_raw_tokens()
        for login_group in login_groups:
            if self.nc_instance.check_scopes(login_group, self.scope_set):
                login_group.update(token_response.by_resource_server)
                break
        self.nc_instance.save_tokens(login_groups)
