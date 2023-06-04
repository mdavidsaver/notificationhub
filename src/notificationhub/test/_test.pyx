# distutils: language = c
#cython: language_level=2

# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

cdef extern from "notificationhub.h":
    struct notifier:
        pass
    int notificationhub_import()
    notifier* notifier_handle(object hub)
    int notifier_poke(notifier* notif) nogil

if notificationhub_import():
    raise ImportError("oops")

def poke(object obj):
    cdef int ret
    cdef notifier* notif = notifier_handle(obj)
    if notif==NULL:
        raise TypeError("Not a Notifier")
    with nogil:
        ret = notifier_poke(notif)
    return ret!=0
