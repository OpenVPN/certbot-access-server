"""Installer plugin for OpenVPN Access Server"""
from typing import Callable, Iterable, Optional, Union, List, Any

from certbot import errors
from certbot.plugins import common
from certbot.compat import os

from .asxmlrpcapi import UnixStreamXMLRPCClient

DEFAULT_SOCKET = "/usr/local/openvpn_as/etc/sock/sagent.localroot"


class Installer(common.Installer):
    """Installer plugin for OpenVPN Access Server.

    This plugin performs installing certificates into Access Server through
    xmlrpc protocol
    """
    description = "OpenVPN Access Server Installer plugin"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.rpc_proxy: Any = None
        super().__init__(*args, **kwargs)

    @classmethod
    def add_parser_arguments(cls, add: Callable[..., None]) -> None:
        add(
            'socket',
            default=DEFAULT_SOCKET,
            type=str,
            help="Socket for connection to OpenVPN Access Server XML-RPC call."
        )
        add(
            'path-only',
            default=False,
            action='store_true',
            help="Upload only cert paths instead of cert body"
        )

    def deploy_cert(self, domain: str, cert_path: str, key_path: str,
                    chain_path: str, fullchain_path: str) -> None:
        if self.conf('path_only'):
            self.rpc_proxy.ConfigPut({'cs.priv_key': key_path})
            self.rpc_proxy.ConfigPut({'cs.cert': cert_path})
            self.rpc_proxy.ConfigPut({'cs.ca_bundle': chain_path})
        else:
            with open(key_path) as f:
                self.rpc_proxy.ConfigPut({'cs.priv_key': f.read()})
            with open(cert_path) as f:
                self.rpc_proxy.ConfigPut({'cs.cert': f.read()})
            with open(chain_path) as f:
                self.rpc_proxy.ConfigPut({'cs.ca_bundle': f.read()})

    def config_test(self) -> None:
        sock_name = self.conf('socket')
        if not os.path.exists(sock_name):
            raise errors.PluginError(
                f"Access Server socket {sock_name} does not exist")

    def enhance(self, domain: str, enhancement: str,
                options: Optional[Union[List[str], str]] = None) -> None:
        pass

    def get_all_names(self) -> Iterable[str]:
        raise errors.NotSupportedError(
            'Access Server plugin does not support automatic domain detection')

    def more_info(self) -> str:
        return 'This plugin installs LetsEncrypt cetificate for HTTPS into ' \
               'OpenVPN Access Server instance'

    def prepare(self) -> None:
        self.config_test()
        self.rpc_proxy = UnixStreamXMLRPCClient(
            self.conf('socket'))

    def restart(self) -> None:
        self.rpc_proxy.RunStart('warm')

    def save(self, title: Optional[str] = None,
             temporary: bool = False) -> None:
        pass

    def supported_enhancements(self) -> List[str]:
        return []
