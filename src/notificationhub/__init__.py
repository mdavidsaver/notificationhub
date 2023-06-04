# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

from array import ArrayType
from errno import EAGAIN, EWOULDBLOCK
import logging
import os
import sys
import threading
from weakref import WeakValueDictionary

from . import _nh

__all__ = (
    'NotificationHub',
    'include_paths',
)

_log = logging.getLogger(__name__)

def pick_array_type():
    for T in 'BHILQ':
        if ArrayType(T).itemsize==4:
            return T
    raise RuntimeError('Unable to find ArrayType for uint32_t')
_array_type = pick_array_type()
del pick_array_type

class Notifier(_nh.Notifier):
    """A handle to trigger notifications through an associated NotificationHub.

       Create by calling NotificationHub.add_notify()

       Notification wakeups are queued.  So multiple calls to poke(),
       or ``notifier_poke()`` may result in only one invocation of
       the provided callback.
    """
    def __init__(self, hub, key, cb):
        self._cb = cb
        _nh.Notifier.__init__(self, hub, key)

class NotificationHub(_nh.NotificationHub):
    """Allows for creation of Notifier instances, and dispatching of notifications.

    :param bool blocking: Controls whether self.handle() will use blocking I/O.
    """
    def __init__(self, blocking=True):
        from . import compat
        self._tx, self._rx = compat.socketpair()
        self._rx.setblocking(blocking)
        _nh.NotificationHub.__init__(self, self._tx.fileno())
        self._rx_buf = b''

        self._lock = threading.Lock() # ensure _next_key and _notif remain consistent
        self._next_key = 0
        self._notif = WeakValueDictionary() # {int:Notifier}

        self._interruptions = 0
        self._interrupt = self.add_notify(self._break)

    if sys.version_info >= (3, 0):
        def __del__(self):
            self.interrupt()
            self._tx.close()
            self._rx.close()

    def fileno(self):
        """Access to the socket read by self.handle()

           When this socket is readable, then self.handle() has work to do.
        """
        return self._rx.fileno()

    def _break(self):
        self._interruptions += 1

    def add_notify(self, cb):
        """Create and return a new Notifier.

           When this Notifier is triggered, the requested callback  `cb` will be
           queued for execution by this NotificationHub.
        """
        with self._lock:
            if len(self._notif)>=0xffffffff:
                raise RuntimeError('Too many Notifiers...')

            K = self._next_key
            assert K not in self._notif, (K, self._notif)

            self._next_key = (self._next_key+1)&0xffffffff
            while self._next_key in self._notif:
                self._next_key = (self._next_key+1)&0xffffffff

            self._notif[K] = ret = Notifier(self, K, cb)

        return ret

    def handle(self):
        """
        """
        while True:
            try:
                buf = self._rx.recv(1024)
            except OSError as e:
                if e.errno in (EAGAIN, EWOULDBLOCK):
                    break
                raise
                
            if buf is None:
                break # _rx closed

            buf = self._rx_buf + buf
            nbytes = len(buf)&~3 # round down to multiple of 4
            self._rx_buf = buf[nbytes:]
            buf = buf[:nbytes]

            for K in ArrayType(_array_type, buf):
                try:
                    notif = self._notif[K]
                except KeyError:
                    continue # ignore dead Notifier

                if not notif._reset():
                    continue # Notifier was not queued?

                try:
                    _log.debug('Notify %r', notif._cb)
                    notif._cb()
                except:
                    _log.exception('Unhandled exception in %r'%notif)

            if self._interruptions>0:
                self._interruptions -= 1
                break

    def interrupt(self):
        """Queue an interruption of a current or future call to self.handle()
        """
        self._interrupt.poke()

def include_paths():
    """List of ``-I`` include paths to find notificationhub.h
    """
    return [
        os.path.dirname(__file__),
    ]
