"""
The `~certbot_access_server.installer_access_server` plugin automates the installing
of obtained certificates to OpenVPN Access Server by communicating with it
throught XmlRPC calls.


Named Arguments
---------------

==========================================  ===================================
``--as-installer-socket``                   Path to socket Access Server is
                                            listening at
                                            (Default: /usr/local/openvpn_as/etc/sock/sagent.localroot)
``--as-installer-path-only``                Load only path to certificate to
                                            Access Server instead of whole
                                            certificate body
                                            (Default: false)
==========================================  ===================================
"""
