# -*- coding: utf-8 -*-
# Debbuild
#
# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#

import os
import shutil
import tempfile
import unittest

from debbuild import debbuild


class TestDebbuild(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = str(tempfile.mkdtemp(prefix='debbuild_test_'))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir)

    def test_debbuild(self):
        with open(os.path.join(self.dir, 'coucou'), 'w') as f:
            f.write('#!/bin/sh')
            f.write('echo coucou')
        debbuild(name='mypackage', version='1.0.1', data_src=self.dir, data_prefix='/opt/mypackage')
