import logging.config

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'basic': {'format': '[%(levelname)s] '
                            '%(name)s::%(funcName)s() %(message)s'}
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'basic',
        }
    },
    'loggers': {
        'fair_research_login': {'level': 'DEBUG', 'handlers': ['console']},
    },
})
