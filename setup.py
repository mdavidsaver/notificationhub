#!/usr/bin/env python

# Copyright 2023 Michael Davidsaver
# See LICENSE
# SPDX-License-Identifier: BSD

import os

from setuptools import setup, Extension
from Cython.Build import cythonize

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as F:
    long_description = F.read()

setup(
    name='notificationhub',
    version='0.0.0a1',
    description='Helper for C extensions to sent notifications from worker threads',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Michael Davidsaver',
    author_email='mdavidsaver@gmail.com',
    license='BSD',

    python_requires='>=2.7',
    install_requires=[
        'Cython',
    ],

    package_dir={'':'src'},
    packages=[
        'notificationhub',
        'notificationhub.test',
    ],
    ext_modules=cythonize([
        Extension('notificationhub._nh', [
                'src/notificationhub/_nh.pyx',
            ]),
        Extension('notificationhub.test._test', [
                'src/notificationhub/test/_test.pyx',
            ],
            include_dirs = ['src/notificationhub'],
        ),
    ]),
    package_data={
        'notificationhub': ['notificationhub.h'],
    },

    zip_safe=False,
)
