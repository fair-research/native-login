# Changes in Fair Research Login


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.

## 0.2.0

### [0.2.0] - Nov 11, 2020

- ``local_server_code_handler`` and ``secondary_code_handler`` replaced by ``code_handlers`` list
- ``set_app_name()`` removed on code_handlers, replaced by ``set_context()``
- ``LocalServerLoginHandler`` now automatically skips and defaults to ``InputCodeHandler``
  if it detects it is running on a remote server
- Added class level set_browser_enabled(True/False) to set global
  setting for enabling/disabling auto-opening the browser. This can
  be done via: `from fair_research_login import CodeHandler` and
  `CodeHandler.set_browser_enabled(False)`
- Browser is automatically disabled if user enters ^C, to avoid taking control away from them more than once.
- User Keyboard interrupt no longer results in calling sys.exit()
- Keyboard interrupt now causes the current code handler to be 'skipped', and the next one in line used.
  By default, this means ``InputCodeHandler`` will be used if the user enters a KeyboardInterrupt for
  ``LocalServerCodeHandler``
- fair_research_login.exc.AuthFailure raised if no code was retrieved and no ``code_handlers`` remain


## 0.1.0

### [0.1.5] - Sept 6, 2019

- Fixed improper expired tokens exception when subset tokens were loaded with refresh

### [0.1.4] - Sept 6, 2019

- Added more examples to docs

### [0.1.3] - Aug 13, 2019

- Fixed improper error being raised if user declined consent when using local server
- Fixed bug where login() would not respect default scopes
- Fixed load_tokens() raising an error if un-requested previously saved tokens had expired
- Fixed login() always starting a flow if un-requested previously saved tokens had expired
- Fixed tokens 'leaking' by revoking old live tokens when a new login is requested before overwrite
- Fixed token leakage by revoking tokens before overwrite
- Fixed login raising ScopesMismatch() exception when more tokens existed than were requested
- Fixed bug if consent was rescinded with refresh tokens


### [0.1.2] - May 24, 2019

- Fixed permissions on builtin token storage to always set user only RW on save
- Fixed load_tokens() not accepting scopes as space separated strings
- Fixed get_authorizers() not accepting requested_scopes

### [0.1.1] - May 17, 2019

- Fixed bug in builtin Config Parser token storage if resource server contained underscores

### [0.1.0] - Feb 13, 2019

- Initial Release!