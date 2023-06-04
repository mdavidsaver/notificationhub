# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

import unittest

from .. import compat

class TestSocketPair(unittest.TestCase):
    def test_actual(self):
        A, B = compat.socketpair()

        self.assertEqual(A.getsockname(), B.getpeername())
        self.assertEqual(B.getsockname(), A.getpeername())

        A.send(b'!')
        self.assertEqual(b'!', B.recv(1))

    def test_compat(self):
        A, B = compat.socketpair_compat()

        self.assertEqual(A.getsockname(), B.getpeername())
        self.assertEqual(B.getsockname(), A.getpeername())

        A.send(b'!')
        self.assertEqual(b'!', B.recv(1))
