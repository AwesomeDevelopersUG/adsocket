import os

DEBUG = True
"""
Enable or disable debug mode
"""

PORT = 5005
#
# ZEENR_API_URL = 'http://zeenr.com/api'
# ZEENR_API_VERSION = 1
#
# SECRET_KEY = "(utc+*0jrzg*+slkx1gx2@&4j&)v^*#n-j(5uez_t=h20h@fun"

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

EXECUTOR_POOL_SIZE = 2

SECURE_PROXY_SSL_HEADER = ('X-Forwarded-Proto', 'https')


CHANNELS = {
    'events': {
        'driver': 'adsocket.ws.channels.Channel',
        'on_startup': False,
    },
    'admin': {
        'driver': 'adsocket.ws.channels.AdminChannel',
        'create_on_startup': True,  # create one instance on application startup
    },
    'global': {
        'driver': 'adsocket.ws.channels.GlobalChannel',
        'create_on_startup': True,
    },
    'user': {
        'driver': 'adsocket.ws.channels.UserChannel',
        'create_on_startup': False,
    },
    'company': {
        'driver': 'adsocket.ws.channels.CompanyChannel',
        'create_on_startup': False,
    }
}

WEBSOCKET_ACTIONS = (
    ('authenticate', 'adsocket.ws.actions.AuthenticateAction'),
    ('subscribe', 'adsocket.ws.actions.JoinAction')
)

WEBSOCKET_CHANNELS = (
    ()
)

REDIS_HOST = 'redis://127.0.0.1'
REDIS_DB = 0
REDIS_MIN_POOL_SIZE = 3
REDIS_MAX_POOL_SIZE = 100

BROKER = {
    'driver': 'adsocket.core.broker.redis.RedisBroker',
    'host': REDIS_HOST,
    'db': REDIS_DB,
    'channels': ['zeenr_ws']
}

AUTHENTICATION_CLASSES = (
    'adsocket.core.auth.ZeenrAuth',
)

DISCONNECT_UNAUTHENTICATED = 30
