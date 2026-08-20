# -*- coding: utf-8 -*-
# Debbuild
#
# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#

import gzip
import os
import shutil
import tarfile
import tempfile
import unittest

from debbuild import DebBuildException, _config, debbuild


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
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            output=tmp,
            depends=['libc6', 'libstdc++6'],
            recommends=['xdg-utils'],
            suggests=['zenity|kdialog'],
            conflicts=['test'],
            provides=['mypackage'],
            breaks=['mypackage<1'],
        )

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

    def test_config(self):
        _config(args=['--name', 'test', '--data-src', f'/opt/mypackage={self.dir}'])

    def test_configfiles_custom(self):
        # Given a build with output
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            config_files=["/opt/mypackage/coucou"],
        )

    def test_debbuild_with_default_changelog(self):
        # Given a build without a custom changelog
        tmp = tempfile.gettempdir()
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            output=tmp,
        )

        # Then the deb archive is created
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))

        # Then the changelog.gz contains the auto-generated content
        content = self._extract_changelog(expected_output)
        self.assertIn('mypackage (1.0.1)', content)
        self.assertIn('Package created with DebBuild.', content)

        os.remove(expected_output)

    def test_debbuild_with_custom_changelog(self):
        # Given a custom changelog file
        changelog_path = os.path.join(self.dir, 'my_changelog')
        custom_content = (
            "mypackage (1.0.1) unstable; urgency=medium\n\n"
            "  * Custom changelog entry for testing.\n\n"
            " -- John Doe <john.doe@example.com>  Mon, 01 Jan 2024 00:00:00 +0000\n"
        )
        with open(changelog_path, 'w') as f:
            f.write(custom_content)

        tmp = tempfile.gettempdir()
        # When building the package with a changelog option
        debbuild(
            name='mypackage',
            version='1.0.1',
            data_src='/opt/mypackage=%s' % (self.dir),
            output=tmp,
            changelog=changelog_path,
        )

        # Then the deb archive is created
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))

        # Then the changelog.gz contains our custom content verbatim
        content = self._extract_changelog(expected_output)
        self.assertEqual(custom_content, content)
        self.assertNotIn('Package created with DebBuild.', content)

        os.remove(expected_output)

    def test_debbuild_with_invalid_changelog(self):
        # Given a changelog path that doesn't exist
        # When creating the archive
        # Then an error is raised
        with self.assertRaises(DebBuildException):
            debbuild(
                name='mypackage',
                version='1.0.1',
                data_src='/opt/mypackage=%s' % (self.dir),
                changelog=os.path.join(self.dir, 'does-not-exist'),
            )

    def test_debbuild_with_changelog_as_directory(self):
        # Given a changelog path pointing to a directory
        # When creating the archive
        # Then an error is raised
        with self.assertRaises(DebBuildException):
            debbuild(
                name='mypackage',
                version='1.0.1',
                data_src='/opt/mypackage=%s' % (self.dir),
                changelog=self.dir,
            )

    def _extract_changelog(self, deb_path):
        """
        Helper to extract and decompress the changelog.gz content from a .deb archive's data.tar.gz.
        """
        extract_dir = tempfile.mkdtemp(prefix='debbuild_extract_')
        try:
            import unix_ar

            ar = unix_ar.open(deb_path)
            try:
                data_info = ar.open('data.tar.gz')
                data_tar_path = os.path.join(extract_dir, 'data.tar.gz')
                with open(data_tar_path, 'wb') as f:
                    f.write(data_info.read())
            finally:
                ar.close()

            with tarfile.open(data_tar_path, 'r:gz') as tar:
                member_name = './usr/share/doc/mypackage/changelog.gz'
                changelog_gz = tar.extractfile(member_name)
                with gzip.open(changelog_gz, 'rt') as f:
                    return f.read()
        finally:
            shutil.rmtree(extract_dir)
