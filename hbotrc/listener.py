import asyncio
from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters
from typing import Any, List, Optional, Tuple, Callable

from .msgs import *
from .spec import TopicSpecs, CommandTopicSpecs


class BotListener(Node):
    def __init__(self,
                 host: str = 'localhost',
                 port: int = 1883,
                 username: str = '',
                 password: str = '',
                 bot_id: str = 'bot1',
                 namespace: str = 'hbot',
                 notifications: bool = True,
                 events: bool = True,
                 logs: bool = True,
                 on_notification: Optional[Callable] = None,
                 on_event: Optional[Callable] = None,
                 on_log: Optional[Callable] = None,
                 on_hb: Optional[Callable] = None,
                 **kwargs
                 ):
        self._notifications = notifications
        self._events = events
        self._logs = logs
        self._bot_id = bot_id
        self._ns = namespace

        if on_notification is not None:
            self._on_notification = on_notification
        if on_event is not None:
            self._on_event = on_event
        if on_log is not None:
            self._on_log = on_log
        if on_hb is not None:
            self._on_hb = on_hb

        topic_prefix = TopicSpecs.PREFIX.format(
            namespace=self._ns,
            instance_id=self._bot_id
        )
        self._hb_topic = f'{topic_prefix}{TopicSpecs.HEARTBEATS}'
        self._notify_topic = f'{topic_prefix}{TopicSpecs.NOTIFICATIONS}'
        self._events_topic = f'{topic_prefix}{TopicSpecs.MARKET_EVENTS}'
        self._logs_topic = f'{topic_prefix}{TopicSpecs.LOGS}'

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

    def _init_endpoints(self):
        if self._notifications:
            self.notify_sub = self.create_subscriber(msg_type=NotifyMessage,
                                                     topic=self._notify_topic,
                                                     on_message=self._on_notification)
            print(f'[*] Subscribed to NOTIFY topic: {self._notify_topic}')
        if self._events:
            self.events_sub = self.create_subscriber(msg_type=EventMessage,
                                                     topic=self._events_topic,
                                                     on_message=self._on_event)
            print(f'[*] Subscribed to EVENT topic: {self._events_topic}')
        if self._logs:
            self.logs_sub = self.create_subscriber(msg_type=LogMessage,
                                                   topic=self._logs_topic,
                                                   on_message=self._on_log)
            print(f'[*] Subscribed to LOG topic: {self._logs_topic}')
        self.hb_sub = self.create_subscriber(msg_type=HeartbeatMessage,
                                             topic=self._hb_topic,
                                             on_message=self._on_hb)
        print(f'[*] Subscribed to HEARTBEAT topic: {self._hb_topic}')

    def _on_notification(self, msg):
        print(f'[NOTIFICATION] - {msg}')

    def _on_event(self, msg):
        print(f'[EVENT] - {msg}')

    def _on_log(self, msg):
        print(f'[LOG] - {msg}')

    def _on_hb(self, msg):
        print(f'[HEARTBEAT] - {msg}')

    def start(self):
        self._init_endpoints()
        self.run()

    async def run_forever(self):
        self.start()
        while True:
            await asyncio.sleep(0.01)
