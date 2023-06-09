from commlib.node import Node
from commlib.transports.mqtt import ConnectionParameters

from .msgs import *
from .spec import TopicSpecs


class BotCommands(Node):
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

        topic_prefix = TopicSpecs.PREFIX.format(
            namespace=self._ns,
            instance_id=self._bot_id
        )
        self._start_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.START}'
        self._stop_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.STOP}'
        self._import_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.IMPORT}'
        self._config_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.CONFIG}'
        self._status_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.STATUS}'
        self._history_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.HISTORY}'
        self._balance_limit_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.BALANCE_LIMIT}'
        self._balance_paper_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.BALANCE_PAPER}'
        self._command_shortcut_uri = f'{topic_prefix}{TopicSpecs.COMMANDS.COMMAND_SHORTCUT}'

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
        self._init_clients()
        self.run()

    def _init_clients(self):
        self._start_cmd = self.create_rpc_client(
            msg_type=StartCommandMessage,
            rpc_name=self._start_uri
        )
        # print(f'[*] Created RPC client for start command @ {self._start_uri}')
        self._stop_cmd = self.create_rpc_client(
            msg_type=StopCommandMessage,
            rpc_name=self._stop_uri
        )
        # print(f'[*] Created RPC client for stop command @ {self._stop_uri}')
        self._import_cmd = self.create_rpc_client(
            msg_type=ImportCommandMessage,
            rpc_name=self._import_uri
        )
        # print(f'[*] Created RPC client for import command @ {self._import_uri}')
        self._config_cmd = self.create_rpc_client(
            msg_type=ConfigCommandMessage,
            rpc_name=self._config_uri
        )
        # print(f'[*] Created RPC client for config command @ {self._config_uri}')
        self._status_cmd = self.create_rpc_client(
            msg_type=StatusCommandMessage,
            rpc_name=self._status_uri
        )
        # print(f'[*] Created RPC client for status command @ {self._status_uri}')
        self._history_cmd = self.create_rpc_client(
            msg_type=HistoryCommandMessage,
            rpc_name=self._history_uri
        )
        # print(f'[*] Created RPC client for history command @ {self._history_uri}')
        self._balance_limit_cmd = self.create_rpc_client(
            msg_type=BalanceLimitCommandMessage,
            rpc_name=self._balance_limit_uri
        )
        # print(f'[*] Created RPC client for balance limit command @ {self._balance_limit_uri}')
        self._balance_paper_cmd = self.create_rpc_client(
            msg_type=BalancePaperCommandMessage,
            rpc_name=self._balance_paper_uri
        )
        # print(f'[*] Created RPC client for balance limit command @ {self._balance_limit_uri}')
        self._command_shortcut_cmd = self.create_rpc_client(
            msg_type=CommandShortcutMessage,
            rpc_name=self._command_shortcut_uri
        )
        # print(f'[*] Created RPC client for command shortcuts @ {self._command_shortcut_uri}')

    def start(self,
              log_level: str = None,
              script: str = None,
              async_backend: bool = False
              ):
        resp = self._start_cmd.call(
            StartCommandMessage.Request(
                log_level=log_level,
                script=script,
                async_backend=async_backend
            )
        )
        return resp

    def stop(self,
             skip_order_cancellation: bool = False,
             async_backend: bool = False
             ):
        resp = self._stop_cmd.call(
            StopCommandMessage.Request(
                skip_order_cancellation=skip_order_cancellation,
                async_backend=async_backend
            )
        )
        return resp

    def import_strategy(self,
                        strategy: str,
                        ):
        resp = self._import_cmd.call(
            ImportCommandMessage.Request(strategy=strategy)
        )
        return resp

    def config(self,
               params: List[Tuple[str, Any]],
               ):
        resp = self._config_cmd.call(
            ConfigCommandMessage.Request(params=params)
        )
        return resp

    def status(self,
               async_backend: bool = False
               ):
        resp = self._status_cmd.call(
            StatusCommandMessage.Request(async_backend=async_backend)
        )
        return resp

    def history(self,
                async_backend: bool = False
                ):
        resp = self._history_cmd.call(
            HistoryCommandMessage.Request(async_backend=async_backend)
        )
        return resp

    def balance_limit(self,
                      exchange: str,
                      asset: str,
                      amount: float
                      ):
        resp = self._balance_limit_cmd.call(
            BalanceLimitCommandMessage.Request(
                exchange=exchange,
                asset=asset,
                amount=amount
            )
        )
        return resp

    def balance_paper(self,
                      asset: str,
                      amount: float
                      ):
        resp = self._balance_paper_cmd.call(
            BalancePaperCommandMessage.Request(
                asset=asset,
                amount=amount
            )
        )
        return resp

    def shortcut(self,
                 params=List[List[Any]]
                 ):
        resp = self._command_shortcut_uri.call(
            CommandShortcutMessage.Request(
                params=params
            )
        )
        return resp
