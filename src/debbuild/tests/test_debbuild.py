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

from debbuild import DebBuildException, debbuild


class TestDebbuild(unittest.TestCase):
    def setUp(self) -> None:
        # Create basic folder structure to be package for testing.
        self.dir = str(tempfile.mkdtemp(prefix='debbuild_test_'))
        with open(os.path.join(self.dir, 'coucou'), 'w') as f:
            f.write('#!/bin/sh')
            f.write('echo coucou')

    def tearDown(self) -> None:
        # Remove the temporary folder.
        shutil.rmtree(self.dir)

    def test_debbuild(self):
        # Given required parameter, debuild run without error.
        debbuild(name='mypackage', version='1.0.1', data_src='/opt/mypackage=%s' % (self.dir))

    def test_debbuild_with_relative_data_src(self):
        # Given a relative data_src
        data_src = self.dir
        data_src = os.path.relpath(data_src, os.getcwd())
        debbuild(name='mypackage', version='1.0.1', data_src='/opt/mypackage=%s' % (self.dir))

    def test_debbuild_with_file_data_src(self):
        # Given a file data_src
        data_src = self.dir
        data_src = os.path.relpath(data_src, os.getcwd())
        debbuild(name='mypackage', version='1.0.1', data_src='/opt/mypackage/bin/coucou=%s/coucou' % (self.dir))

    def test_debbuild_with_output(self):
        tmp = tempfile.gettempdir()
        # Given a build with output
        debbuild(name='mypackage', version='1.0.1', data_src='/opt/mypackage=%s' % (self.dir), output=tmp)
        # Then file is created in output
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))
        os.remove(expected_output)

    def test_debbuild_with_symlink_as_string(self):
        # Given a build with output
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            symlink=["/usr/bin/mypackage=/opt/mypackage/coucou"],
        )

    def test_debbuild_with_symlink_as_tuple(self):
        # Given a build with output
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            symlink=[("/usr/bin/mypackage", "/opt/mypackage/coucou")],
        )

    def test_debbuild_with_empty_data_src(self):
        # Given a symlink with empty value
        # When creating the archive
        # Then an error is raised
        with self.assertRaises(DebBuildException):
            debbuild(
                name='mypackage',
                version='1.0.1',
                data_src='/opt/mypackage=',
            )

    def test_debbuild_with_empty_symlink(self):
        # Given a symlink with empty value
        # When creating the archive
        # Then an error is raised
        with self.assertRaises(DebBuildException):
            debbuild(
                name='mypackage',
                version='1.0.1',
                data_src='/opt/mypackage=%s' % (self.dir),
                symlink=[("/usr/bin/mypackage", "")],
            )
