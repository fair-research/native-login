# Changelog

All notable changes to this project will be documented in this file. See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

### [0.2.4](https://github.com/fair-research/native-login/compare/v0.2.3...v0.2.4) (2021-10-19)


### Bug Fixes

* login() improperly catching broad exceptions ([013a49c](https://github.com/fair-research/native-login/commit/013a49c7135ca14e0982503f133a63fc2a261490))
* login() improperly catching broad load errors on token save ([ae14190](https://github.com/fair-research/native-login/commit/ae141908d839089185f21001422cd8a1980370d5))

### [0.2.3](https://github.com/fair-research/native-login/compare/v0.2.2...v0.2.3) (2021-09-23)


### Features

* Add support for Globus SDK v3 ([b26b6f2](https://github.com/fair-research/native-login/commit/b26b6f230aecbdd281d6011ed1c0624c39e60118))


### Bug Fixes

* Globus SDK v3 compatibility 'query_params' ([f566350](https://github.com/fair-research/native-login/commit/f566350f6baf5b5527587a30d94ca15d947b0aa6))
* Support for Globus SDK v3 ([00cc2f8](https://github.com/fair-research/native-login/commit/00cc2f8fae8c0c07709217b1a27f376d36cad4bb))

### [0.2.2](https://github.com/fair-research/native-login/compare/v0.2.1...v0.2.2) (2021-06-29)


### Bug Fixes

* Disallow Globus SDK version 3 ([b2b38bc](https://github.com/fair-research/native-login/commit/b2b38bc4f650ba1ac4e74549fd5abc11a3e606aa))

### [0.2.1](https://github.com/fair-research/native-login/compare/v0.2.0...v0.2.1) (2021-06-17)


### Bug Fixes

* Include six as a dependency ([f09cc68](https://github.com/fair-research/native-login/commit/f09cc68c9e26f1b3d2ef2ea5f1d3096771b231d1))
* logging being overly verbose on [info]. Moved to [debug] ([778ae65](https://github.com/fair-research/native-login/commit/778ae65e4ca108b4fc65222a3c464cf0a50e910f))
* Tests being included in wheels ([efff487](https://github.com/fair-research/native-login/commit/efff487caab6b2c8d8134c5d9c8c16fbd6480cce))

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