import asyncio
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters
from typing import Any, List, Optional, Tuple, Callable
from pydantic import BaseModel

from .msgs import ExternalEvent
from .spec import TopicSpecs, CommandTopicSpecs


class BotEventEmitter(Node):
    def __init__(self,
                 bot_id: str,
                 host: str = 'localhost',
                 port: int = 1883,
                 username: str = '',
                 password: str = '',
                 namespace: str = 'hbot',
                 **kwargs
                 ):
        self._bot_id = bot_id
        self._ns = namespace
        self._pub = None

        _prefix = TopicSpecs.PREFIX.format(
            namespace=self._ns,
            instance_id=self._bot_id
        )
        self._uri_prefix = f'{_prefix}{TopicSpecs.EXTERNAL_EVENTS[:-1]}'

        conn_params = ConnectionParameters(
            host=host,
            port=int(port),
            username=username,
            password=password
        )

        super().__init__(
            node_name=f'{self._ns}.{self._bot_id}',
            connection_params=conn_params,
            heartbeats=False,
            debug=True,
            **kwargs
        )
        self._init_publisher()
        self.run()

    def _event_name_to_uri(self, event_name: str) -> str:
        uri = f'{self._uri_prefix}{event_name}'
        return uri

    def _init_publisher(self):
        self._pub = self.create_mpublisher()
        self._pub.run()

    def _publish_event(self, event: ExternalEvent):
        _uri = self._event_name_to_uri(event.name.replace('.', '/'))
        _data = event.dict()
        # Remove name property from message. Only used on client
        _data.pop('name')
        self._pub.publish(_data, _uri)

    def send(self, event: ExternalEvent):
        self._publish_event(event)
