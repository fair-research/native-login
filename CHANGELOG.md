# Changes in Fair Research Login


Below are major changes for each version Release. For detailed information,
see the list of commits from the last version or use `git log`.


## 0.1.0

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