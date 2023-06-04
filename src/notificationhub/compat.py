# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

__all__ = (
    'socketpair',
)

import socket
def socketpair_compat(family=None, stype=socket.SOCK_STREAM, proto=0):
    import socket
    from threading import Thread

    if family not in (socket.AF_INET, None) or stype!=socket.SOCK_STREAM:
        raise NotImplementedError("Only AF_INET, SOCK_STREAM currently supported")
    family = socket.AF_INET

    serv = socket.socket(family, stype, proto)
    serv.bind(('127.0.0.1', 0))
    serv.listen(4)
    serv_ep = serv.getsockname()

    sess = [(None, None)]
    def accept(serv=serv, sess=sess):
        sess[0] = serv.accept()

    while True:
        cli = socket.socket(family, stype, proto)

        acceptor = Thread(target=accept)
        acceptor.start()

        try:
            cli.connect(serv_ep)

        except:
            serv.close() # hope this interrupts the accept...
        finally:
            acceptor.join()
            serv.close()

        S, peer = sess[0]
        if peer != cli.getsockname():
            cli.close() # retry...
        else:
            return cli, S

del socket

try:
    from socket import socketpair
except ImportError:
    socketpair = socketpair_compat
