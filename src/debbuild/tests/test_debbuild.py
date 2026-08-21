# debbuild: Pure-Python DEB package builder.
# Copyright (C) 2025-2026 Patrik Dufresne <patrik@ikus-soft.com>
#
# SPDX-License-Identifier: MIT

import datetime
import gzip
import os
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

from debbuild import DebBuildException, _config, debbuild

LINTIAN = shutil.which('lintian')


class TestDebbuild(unittest.TestCase):
    def setUp(self) -> None:
        # Create basic folder structure to be package for testing.
        self.dir = str(tempfile.mkdtemp(prefix='debbuild_test_'))
        coucou_exe = Path(self.dir) / "coucou"
        with open(coucou_exe, 'w') as f:
            f.write('#!/bin/sh\n')
            f.write('echo coucou\n')
        Path(self.dir).chmod(0o0755)
        coucou_exe.chmod(0o0755)

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
            architecture='all',
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
            architecture='all',
            output=tmp,
        )

        # Then the deb archive is created
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))

        # Then the changelog.Debian.gz contains the auto-generated content
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
            architecture='all',
        )

        # Then the deb archive is created
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))

        # Then the changelog.Debian.gz contains our custom content verbatim
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

    @unittest.skipUnless(LINTIAN, 'required lintian')
    def test_lintian(self):
        # Given we create a package
        debbuild(
            name='mypackage',
            url="http://homepage.com",
            description="This is a test package",
            maintainer="Patrik <patrik@ikus-soft.com>",
            long_description="This is a long description" * 10,
            version='1.0.1',
            data_src='/usr/libexec=%s' % (self.dir),
        )
        # When running lintian
        subprocess.check_call([LINTIAN, '-I', 'mypackage_1.0.1_all.deb'])
        # Then no error get raised

    def test_license_with_mit(self):
        # When a package is generated with a license-name
        tmp = tempfile.gettempdir()
        debbuild(
            name='mypackage',
            url="http://homepage.com",
            description="This is a test package",
            maintainer="Patrik <patrik@ikus-soft.com>",
            long_description="This is a long description" * 10,
            version='1.0.1',
            data_src='/usr/libexec=%s' % (self.dir),
            license_name='MIT',
            architecture='all',
            output=tmp,
        )
        expected_output = os.path.join(tmp, "mypackage_1.0.1_all.deb")
        self.assertTrue(os.path.isfile(expected_output))
        # Then pacakge include a copyright file.
        content = self._extract_copyright(expected_output)
        current_year = datetime.datetime.now().year
        self.assertEqual(
            content.decode(),
            f"""Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: mypackage
Upstream-Contact: Patrik <patrik@ikus-soft.com>
Source: http://homepage.com

Files: *
Copyright: {current_year} Patrik <patrik@ikus-soft.com>
License: MIT
 The MIT License (MIT)
 .
 Copyright (c) {current_year} Patrik <patrik@ikus-soft.com>
 .
 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:
 .
 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.
 .
 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.
""",
        )

    def test_debbuild_architecture(self):
        # When creating a deb with default architecture.
        tmp = tempfile.gettempdir()
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
            architecture='amd64',
        )

        # Then file is created with amd64
        expected_output = os.path.join(tmp, "mypackage_1.0.1_amd64.deb")
        self.assertTrue(os.path.isfile(expected_output))

    def _extract_changelog(self, deb_path):
        return self._extract_file_content(deb_path, './usr/share/doc/mypackage/changelog.Debian.gz')

    def _extract_copyright(self, deb_path):
        return self._extract_file_content(deb_path, './usr/share/doc/mypackage/copyright')

    def _extract_file_content(self, deb_path, member_name):
        """
        Helper to extract and decompress the changelog.Debian.gz content from a .deb archive's data.tar.gz.
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
                fn = tar.extractfile(member_name)
                if member_name.endswith('.gz'):
                    with gzip.open(fn, 'rt') as f:
                        return f.read()
                else:
                    return fn.read()
        finally:
            shutil.rmtree(extract_dir)
