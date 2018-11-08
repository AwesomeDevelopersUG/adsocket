import os

DEBUG = False
"""
Enable or disable debug mode
"""

PORT = 5005

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        }
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
        }
    },
    'loggers': {
        'adsocket': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True
        },
        'aiohttp': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': True
        }
    },
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')


CHANNELS = {
    'ping': {
        'driver': 'adsocket.core.channels.Channel',
        'on_startup': False,
    },
}

WEBSOCKET_ACTIONS = (
    ('authenticate', 'adsocket.ws.actions.AuthenticateAction'),
    ('subscribe', 'adsocket.ws.actions.JoinAction')
)


REDIS_HOST = 'redis://127.0.0.1'
REDIS_DB = 0
REDIS_MIN_POOL_SIZE = 3
REDIS_MAX_POOL_SIZE = 100

BROKER = {
    'driver': 'adsocket.core.broker.redis.RedisBroker',
    'host': REDIS_HOST,
    'db': REDIS_DB,
    'channels': ['adsocket']
}

AUTHENTICATION_CLASSES = []

DISCONNECT_UNAUTHENTICATED = False
