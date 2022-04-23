"""Transport for communicating with xmlrpc through unix socket"""
from typing import Any

import socket
import xmlrpc.client
from http.client import HTTPConnection


class UnixStreamHTTPConnection(HTTPConnection):
    """A class to make http connection through unix socket"""
    def connect(self) -> None:
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect(self.host)


class UnixStreamTransport(xmlrpc.client.Transport):
    """A wrapper for xmlrpc transport to use unix socket"""
    def __init__(self, socket_path: str) -> None:
        self.socket_path = socket_path
        super().__init__()

    def make_connection(self, _: Any) -> HTTPConnection:
        return UnixStreamHTTPConnection(self.socket_path)


class UnixStreamXMLRPCClient(xmlrpc.client.ServerProxy):
    """Hack to avoid 'unsupported XML-RPC protocol' error"""
    def __init__(self, addr: str, **kwargs: Any) -> None:
        transport = UnixStreamTransport(addr)
        # For some reason xmlrpc.client.ServerProxy __init__ raises an Exception
        # if scheme isn't 'http' or 'https'
        # So we're adding explicit 'http://' as a uri despite that it isn't
        # needed when connecting through a socket
        super().__init__(
            "http://", transport=transport, **kwargs
        )
