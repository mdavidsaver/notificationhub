# distutils: language = c
#cython: language_level=2

# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

cimport cython

from libc.string cimport memset
from libc.stdint cimport uint8_t, uint32_t

from cpython.pycapsule cimport PyCapsule_New

cdef extern from "notificationhub.h":
    int NOTIFICATIONHUB_ABI_VERSION

abi_version = NOTIFICATIONHUB_ABI_VERSION

cdef extern from "compat.h":
    struct Mutex:
        pass
    int MutexInit(Mutex*) nogil
    void MutexFinalize(Mutex*) nogil
    void MutexLock(Mutex*) nogil
    void MutexUnlock(Mutex*) nogil

    ctypedef int SOCKET
    SOCKET INVALID_SOCKET

    int SockSend(SOCKET tx, void* buf, size_t size) nogil

cdef struct HubImpl:
    SOCKET tx

cdef struct NotifierImpl:
    HubImpl* hub
    uint32_t key
    Mutex lock
    uint8_t queued

cdef NotifierImpl* notifier_handle_impl(Notifier notif) except NULL:
    cdef Notifier pvt = notif

    if pvt is None:
        return NULL

    return &notif.impl

notifier_handle = PyCapsule_New(&notifier_handle_impl, "notifier* (PyObject*)", NULL)

cdef int notifier_poke_impl(NotifierImpl* notif) nogil:
    cdef int ret = 0
    MutexLock(&notif.lock)
    try:
        if not notif.queued:
            SockSend(notif.hub.tx, &notif.key, sizeof(notif.key))
            notif.queued = ret = 1
    finally:
        MutexUnlock(&notif.lock)
    return ret

notifier_poke = PyCapsule_New(&notifier_poke_impl, "int (notifier*)", NULL)

@cython.no_gc_clear # due to "shadow" reference self.impl.hub
cdef class Notifier:
    cdef NotifierImpl impl
    cdef readonly NotificationHub hub

    def __cinit__(self, *args, **kws):
        memset(&self.impl, 0, sizeof(self.impl))
        if MutexInit(&self.impl.lock):
            raise RuntimeError("Unable to initialize Mutex")

    def __init__(self, NotificationHub hub, int key):
        self.hub = hub
        self.impl.key = key
        self.impl.hub = &hub.impl

    def __dealloc__(self):
        MutexFinalize(&self.impl.lock)

    def poke(self):
        """Queue this notification.

           Fully re-entrant.
           May be called from a signal handler.
        """
        cdef int ret
        cdef NotifierImpl* impl = notifier_handle_impl(self)
        with nogil:
            ret = notifier_poke_impl(impl)
        return ret!=0

    def _reset(self):
        cdef uint8_t queued
        MutexLock(&self.impl.lock)
        queued = self.impl.queued
        self.impl.queued = 0
        MutexUnlock(&self.impl.lock)
        return queued!=0

cdef class NotificationHub:
    cdef HubImpl impl

    def __cinit__(self):
        memset(&self.impl, 0, sizeof(self.impl))
        self.impl.tx = INVALID_SOCKET

    def __init__(self, int tx): # tx handled as borrowed reference (from subclass)
        self.impl.tx = tx
