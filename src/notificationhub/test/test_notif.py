# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

import gc
import os
import platform
import threading
import unittest
import weakref

from .. import _nh
from .. import NotificationHub, include_paths

class TestPath(unittest.TestCase):
    def test_include_paths(self):
        paths = include_paths()
        self.assertNotEqual([], paths)
        for path in paths:
            self.assertTrue(os.path.isdir(path), "path: %r"%path)

class TestHub(unittest.TestCase):
    if platform.python_implementation()!='PyPy': # I don't know how to test GC behavior w/ pypy.
        @staticmethod
        def _garbage():
            gc.collect()
            everything = gc.get_objects()
            ret = {obj for obj in everything if isinstance(obj, (_nh.NotificationHub, _nh.Notifier))}
            return ret

        def assertNoNotif(self):
            self.assertSetEqual(set(), self._garbage())

        def setUp(self):
            self._leftOvers = {weakref.ref(obj) for obj in self._garbage()}

        def tearDown(self):
            leftOvers = {obj() for obj in self._leftOvers}
            if None in leftOvers:
                self.fail("Some leftovers expired during a later test...  Race condition :( %r", leftOvers)
            newJunk = self._garbage().difference(leftOvers)
            self.assertSetEqual(set(), newJunk)

        def test_gc1(self):
            H = NotificationHub()

        def test_gc2(self):
            H = NotificationHub()
            N = H.add_notify(lambda:None)

        def test_gc3(self):
            H = NotificationHub()
            def stupid(H=H): # creates a strong reference loop
                pass
            N = H.add_notify(stupid)

    def test_wake(self):
        evt = threading.Event()
        wakes = [0]
        def inc(wakes=wakes, evt=evt):
            wakes[0] += 1
            evt.set()

        H = NotificationHub()
        T = threading.Thread(target=H.handle)
        T.start()
        try:
            N = H.add_notify(inc)

            self.assertTrue(N.poke())

            while wakes[0]==0:
                evt.wait()

        finally:
            H.interrupt()
            T.join()

    def test_wake_api(self):
        from . import _test
        evt = threading.Event()
        wakes = [0]
        def inc(wakes=wakes, evt=evt):
            wakes[0] += 1
            evt.set()

        H = NotificationHub()
        T = threading.Thread(target=H.handle)
        T.start()
        try:
            N = H.add_notify(inc)

            self.assertTrue(_test.poke(N))

            while wakes[0]==0:
                evt.wait()

        finally:
            H.interrupt()
            T.join()
