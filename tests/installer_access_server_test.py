import sys
import socket


try:
    import mock
except ImportError:  # pragma: no cover
    from unittest import mock  # type: ignore

import pytest

from certbot import errors
from certbot.compat import os
from certbot_access_server._internal.installer_access_server import Installer
from certbot_access_server._internal import asxmlrpcapi

CERT_PATH = 'testdata/cert.txt'
CA_BUNDLE_PATH = 'testdata/ca_bundle.txt'
PRIV_KEY_PATH = 'testdata/priv_key.txt'


def _expand_path(path):
    return os.path.join(os.path.dirname(__file__), path)


SOCKET_PATH = '/tmp/access_server_test.sock'
RPC_HEAD = (
    b'POST /RPC2 HTTP/1.1\r\nHost: /tmp/access_server_test.sock\r\n'
    b'Accept-Encoding: gzip\r\nContent-Type: text/xml\r\nUser-Agent: Python-xmlrpc/%d.%d\r\n'
    b'Content-Length: %%d\r\n\r\n' % sys.version_info[:2]
)

RPC_RESTART = (
    b"<?xml version='1.0'?>\n<methodCall>\n<methodName>RunStart</methodName>\n<params>\n"
    b"<param>\n<value><string>warm</string></value>\n</param>\n</params>\n</methodCall>\n"
)

RPC_CONFIG_PUT = (
    b"<?xml version='1.0'?>\n<methodCall>\n<methodName>ConfigPut</methodName>\n<params>\n<param>\n"
    b"<value><struct>\n<member>\n<name>%s</name>\n<value><string>%s</string></value>\n</member>\n"
    b"</struct></value>\n</param>\n</params>\n</methodCall>\n"
)

DEFAULT_PARAMS = {
    'access_server_socket': SOCKET_PATH,
    'access_server_path_only': True,
}


def _get_content():
    yield (b"<?xml version='1.0'?>\n<methodResponse>\n<params>\n<param>\n"
           b"<value><nil/></value></param>\n</params>\n</methodResponse>\n")
    yield None


class MockResponse:
    def __init__(self):
        self.status = 200
        self.__content = _get_content()

    def getheader(self, *_):
        return ''

    def read(self, _):
        return next(self.__content)


@pytest.fixture
def sock():
    open(SOCKET_PATH, 'a').close()
    yield
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)


@pytest.fixture
def make_installer(sock):
    def installer(**params):
        params = dict(DEFAULT_PARAMS, **params)
        config = mock.MagicMock(**params)
        inst = Installer(config, 'access-server')
        inst.prepare()
        return inst
    return installer


def test_deploy_cert(make_installer, monkeypatch):
    installer = make_installer()
    with monkeypatch.context() as m:
        test_mock = mock.MagicMock()
        m.setattr(socket, 'socket', test_mock)
        m.setattr(asxmlrpcapi.HTTPConnection, 'getresponse', lambda _: MockResponse())
        installer.deploy_cert(
            'test',
            _expand_path(CERT_PATH),
            _expand_path(PRIV_KEY_PATH),
            _expand_path(CA_BUNDLE_PATH), ''
        )
    cs_priv_call = RPC_CONFIG_PUT % (b'cs.priv_key', _expand_path(PRIV_KEY_PATH).encode())
    cs_cert_call = RPC_CONFIG_PUT % (b'cs.cert', _expand_path(CERT_PATH).encode())
    cs_ca_call = RPC_CONFIG_PUT % (b'cs.ca_bundle', _expand_path(CA_BUNDLE_PATH).encode())
    expected = [
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_priv_call)),
        mock.call().sendall(cs_priv_call),
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_cert_call)),
        mock.call().sendall(cs_cert_call),
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_ca_call)),
        mock.call().sendall(cs_ca_call)
    ]
    assert test_mock.mock_calls == expected


def test_deploy_cert_body(make_installer, monkeypatch):
    installer = make_installer(access_server_path_only=False)
    with monkeypatch.context() as m:
        test_mock = mock.MagicMock()
        m.setattr(socket, 'socket', test_mock)
        m.setattr(asxmlrpcapi.HTTPConnection, 'getresponse', lambda _: MockResponse())
        installer.deploy_cert(
            'test',
            _expand_path(CERT_PATH),
            _expand_path(PRIV_KEY_PATH),
            _expand_path(CA_BUNDLE_PATH), ''
        )
    cs_priv_call = RPC_CONFIG_PUT % (b'cs.priv_key', b'priv_key_content\n')
    cs_cert_call = RPC_CONFIG_PUT % (b'cs.cert', b'cert_content\n')
    cs_ca_call = RPC_CONFIG_PUT % (b'cs.ca_bundle', b'ca_bundle_content\n')
    expected = [
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_priv_call)),
        mock.call().sendall(cs_priv_call),
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_cert_call)),
        mock.call().sendall(cs_cert_call),
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(cs_ca_call)),
        mock.call().sendall(cs_ca_call)
    ]
    assert test_mock.mock_calls == expected


def test_restart(make_installer, monkeypatch):
    installer = make_installer()
    with monkeypatch.context() as m:
        test_mock = mock.MagicMock()
        m.setattr(socket, 'socket', test_mock)
        m.setattr(asxmlrpcapi.HTTPConnection, 'getresponse', lambda _: MockResponse())
        installer.restart()
    expected = [
        mock.call(socket.AF_UNIX, socket.SOCK_STREAM),
        mock.call().connect(SOCKET_PATH),
        mock.call().sendall(RPC_HEAD % len(RPC_RESTART)),
        mock.call().sendall(RPC_RESTART)
    ]
    assert test_mock.mock_calls == expected


def test_incorrect_socket(make_installer):
    with pytest.raises(errors.PluginError):
        make_installer(access_server_socket='/incorrect/socket/path/')
