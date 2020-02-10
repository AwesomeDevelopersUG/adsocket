# ADSocket

WebSocket server based on [aiohttp](https://github.com/aio-libs/aiohttp).


## Install

Using python package

``` bash
pip install adsocket
```

## How it works

To start the very basic server, this command will do:
 ``` bash
adsocket
```
assuming that you have redis server started on localhost listening on port 6379.

Now you should be able to connect to server on ws://localhost:5000

## Basic usage

Adsocket should work out of the box, however it's probably not what you would expect. 
To customize adsocket you can create custom channels, authentication or commands.

Example of setting file

```python
from adsocket.conf.default_settings import *  # NOQA

CHANNELS = {
    'global': {
        'driver': 'my_package.channels.GlobalChannel',
        'create_on_startup': True,
    },
    'user': {
        'driver': 'my_package.channels.MyUserChannel',
        'create_on_startup': False,
    }
}

AUTHENTICATION_CLASSES = (
    'sraps_socket.auth.SrapsAuth',
)

DISCONNECT_UNAUTHENTICATED = False

```
To apply changes to adsocket you need to export environment variable with 
path to settings

 ``` bash
export ADSOCKET_SETTINGS=my_package.settings
```

## Sending messages from you application

See [adsocket-transport](https://github.com/AwesomeDevelopersUG/adsocket-transport).

## Documentation

@Todo

## Goals
Out motivation to behind is follows:
 * High scalability
 * High performance
 * Easy customization
 * Easy extendability

### Channels

All communication between server and client is through channels. 
Any client (understand websocket connection) can be member of n channels. 
There is no automatic subscription to channel so in order ot receive messages 
from server client have to subscribe to channels he or she wants to receive 
messages from or publish messages to.

#### Custom channels

@Todo

 
### Commands

@Todo

#### Custom command

@Todo
