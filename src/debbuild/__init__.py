# -*- coding: utf-8 -*-
# Debbuild
#
# Copyright (C) 2021 IKUS Software inc. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
import argparse
import datetime
import gzip
import hashlib
import os
import shutil
import stat
import tarfile

import jinja2
import unix_ar

STAGING_DIR = "staging"

DEFAULT_BUILD_DIR = ".debbuild"

DEFAULT_VERSION = "1.0"

DEFAULT_DEB = "{{name}}_{{version}}_{{architecture}}.deb"

DEFAULT_ARCHITECTURE = "all"

DEFAULT_DISTRIBUTION = "unstable"

DEFAULT_MAINTAINER = "ChangeMe <info@example.com>"

DEFAULT_URL = "http://no-url-given.example.com/"

DEFAULT_DESCRIPTION = "no description given"

DEFAULT_LONG_DESCRIPTION = "No long description given for this package."

TMPL_CONTROL = """Package: {{name}}
Version: {{version}}
Section: misc
Priority: optional
Architecture: {{architecture}}
Depends: {{ ', '.join(depends) }}
Maintainer: {{maintainer}}
Homepage: {{ url }}
Description: {{ description|replace("\n", " ") }}
{%- filter indent(width=1) %}
{{ long_description | replace("\n", " ") | wordwrap(78) }}
{% endfilter -%}
"""

TMPL_CHANGELOG = """{{name}} ({{version}}) {{distribution}}; urgency=medium

  * Package created with DebBuild.

 -- {{maintainer}}  {{source_date.strftime("%a, %d %b %Y %T %z")}}
"""


class DebBuildException(Exception):
    pass


def _filter(mode=None, mask=None, uid=0, gui=0, uname="root", gname="root"):
    """
    Used to apply proper attribute to file archived.
    """

    def _filter(tarinfo):
        if mode is not None:
            tarinfo.mode = mode
        if mask is not None:
            tarinfo.mode = tarinfo.mode & mask
        tarinfo.uid = uid
        tarinfo.gid = gui
        tarinfo.gname = uname
        tarinfo.uname = gname
        return tarinfo

    return _filter


def _isfile(path):
    """
    Return True if ans only if the path is a file. Doesn't follow symlink.
    """
    try:
        st = os.stat(path, follow_symlinks=False)
    except (OSError, ValueError):
        return False
    return stat.S_ISREG(st.st_mode)


def _isdir(path):
    """
    Return True if ans only if the path is a file. Doesn't follow symlink.
    """
    try:
        st = os.stat(path, follow_symlinks=False)
    except (OSError, ValueError):
        return False
    return stat.S_ISDIR(st.st_mode)


def _config():
    parser = argparse.ArgumentParser(
        prog="debbuild",
        description="TODO",
    )
    parser.add_argument(
        "--name",
        help="name of the package",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--url",
        help="Homepage of this project",
        default=DEFAULT_URL,
        type=str,
    )
    parser.add_argument(
        "--description",
        help="short package description",
        type=str,
        default=DEFAULT_DESCRIPTION,
    )
    parser.add_argument(
        "--long-description",
        help="long package description",
        type=str,
        default=DEFAULT_LONG_DESCRIPTION,
    )
    parser.add_argument(
        "--maintainer",
        help="The maintainer of this package. e.g.: John Wick <john.wick@example.com>",
        type=str,
        default=DEFAULT_MAINTAINER,
    )
    parser.add_argument(
        "--output",
        help="Define the directory of the debian package. Default to current working directory",
        type=str,
    )
    parser.add_argument(
        "--deb",
        help="The debian package to be generated. Default to `<name>_<version>_all.deb`.",
        default=DEFAULT_DEB,
        type=str,
    )
    parser.add_argument(
        "--version",
        help="Package version.",
        default=DEFAULT_VERSION,
        type=str,
    )
    parser.add_argument(
        "--data-src",
        help="The directory to include in the package. This flag can be specified multiple times. Must be define as <destination>=<path>. If you data is located in `./build/mypackage` and you want your application to be installed in `/opt/mypackage`, data should be defined as `--data /opt/mypackage=./build/mypackage`",
        required=True,
        action='append',
        type=str,
    )
    parser.add_argument(
        "--build-dir",
        help="Temporary location where to build the archive",
        default=DEFAULT_BUILD_DIR,
        type=str,
    )
    parser.add_argument(
        "--preinst",
        help="A script to be run before package installation",
        type=str,
    )
    parser.add_argument(
        "--postinst",
        help="A script to be run after package installation",
        type=str,
    )
    parser.add_argument(
        "--prerm",
        help="A script to be run before package removal",
        type=str,
    )
    parser.add_argument(
        "--postrm",
        help=" script to be run after package removal to purge remaining (config) files",
        type=str,
    )
    parser.add_argument(
        "--architecture",
        help="The architecture name. Usually matches `uname -m`. e.g.: all, amd64, i386",
        type=str,
        default=DEFAULT_ARCHITECTURE,
    )
    parser.add_argument(
        "--distribution",
        help="Set the Debian distribution. Default: unstable",
        type=str,
        default=DEFAULT_DISTRIBUTION,
    )
    parser.add_argument(
        "--symlink",
        "--link",
        help="Define a symlink to be created as `<link>=<target>` This flag can be specified multiple times. e.g.: `--symlink /opt/mypackage/bin/mypackage=/usr/bin/mypackage`",
        action='append',
        type=str,
    )
    parser.add_argument(
        "--depends",
        help="A dependency. This flag can be specified multiple times. e.g.: `--depends `",
        action='append',
        type=str,
        default=[],
    )
    return parser.parse_args()


def _as_tuple(value, error_message):
    """
    Used to read --data-src and --symlink configuration that could be define as string, list of string or list of tuple.
    """
    if value:
        # Support a single string value.
        if isinstance(value, str):
            value = [value]
        # Loop on each data source
        for item in value:
            # Item could be a tuple with source and dest or a string to be split.
            try:
                try:
                    k, v = item
                except ValueError:
                    k, v = item.partition('=')[0::2]
            except ValueError:
                raise DebBuildException(error_message)
            # Raise an error if key or value is empty.
            if not k or not v:
                raise DebBuildException(error_message)
            yield k, v


def _template(tmpl, **kwargs):
    t = jinja2.Environment().from_string(tmpl)
    return t.render(**kwargs)


def _debian_binary(build_dir, **kwargs):
    """
    debian-binary contains the version.
    """
    filename = os.path.join(build_dir, "debian-binary")
    with open(filename, "w") as f:
        f.write("2.0\n")
    return filename


def _control_tar(build_dir, **kwargs):
    """
    Create control.tar.gz
    """
    filename = os.path.join(build_dir, "control.tar.gz")
    f = tarfile.open(filename, "w:gz", format=tarfile.GNU_FORMAT)

    # Write control script
    f.add(_write_control(build_dir=build_dir, **kwargs), arcname="./control", filter=_filter(mode=0o644))

    # Write md5sum
    f.add(_write_control_md5sums(build_dir=build_dir, **kwargs), arcname="./md5sums", filter=_filter(mode=0o644))

    # Add post & pre scripts
    for script in ["preinst", "postinst", "prerm", "postrm"]:
        if not kwargs.get(script, None):
            continue
        path = kwargs[script]
        if not _isfile(path):
            raise DebBuildException("%s script `%s` must be a file" % (script, path))
        f.add(path, arcname="./" + script, filter=_filter(mode=0o755))

    # Close archive to flush data on disk.
    f.close()
    return filename


def _write_control(build_dir, **kwargs):
    """
    Create a control file from template.
    """
    filename = os.path.join(build_dir, "control")
    with open(filename, "w") as c:
        data = _template(TMPL_CONTROL, **kwargs)
        c.write(data)
        # Write required final newline
        if not data.endswith("\n"):
            c.write("\n")
    return filename


def _write_control_md5sums(build_dir, **kwargs):
    """
    Generate md5sum for all files.
    """
    filename = os.path.join(build_dir, "md5sums")
    first = True
    with open(filename, "w") as f:
        for path, target in _walk(**kwargs):
            if _isfile(path):
                with open(path, "rb") as input:
                    md5_value = hashlib.md5(input.read()).hexdigest()
                # Print newline between file only
                if first:
                    first = False
                else:
                    f.write("\n")
                # md5hash + 2 spaces + filename without ./
                f.write(md5_value)
                f.write("  ")
                f.write(target[2:])
    return filename


def _write_changelog(name, staging_dir, **kwargs):
    """
    Create a changelog.gz
    """
    filename = os.path.join(staging_dir, f"usr/share/doc/{name}/changelog.gz")
    os.makedirs(os.path.dirname(filename))
    with gzip.open(filename, "w") as f:
        f.write(_template(TMPL_CHANGELOG, name=name, **kwargs).encode("utf-8"))
    return filename


def _write_symlink(symlink, staging_dir, **kwargs):
    """
    Create the symlink in staging folder.
    """
    # Loop on symlink
    for link, target in _as_tuple(symlink, 'expect symlink to be define as <link>=<target>'):
        # Make the path relative
        link = os.path.join(staging_dir, link.strip('/'))
        # Create missing directories
        os.makedirs(os.path.dirname(link), exist_ok=True)
        # Finally create the symlink.
        os.symlink(target, link)


def _walk(data_src, staging_dir, **kwargs):
    """
    Used to walk trought the data directory by listing it's content recursively.
    """
    # Loop on each data source
    for prefix, data in _as_tuple(data_src, 'expect `data-src` to be define as <prefix>=<data>'):

        # Validate Path
        if not (_isfile(data) or _isdir(data)):
            raise DebBuildException("data-src path `%s` must be a file or directory" % data)

        # Make sure prefix start with dot (.)
        if not prefix.startswith("."):
            prefix = ("." if prefix.startswith("/") else "./") + prefix

        # Yield intermediate directories
        for i in range(1, len(prefix.split("/"))):
            path = data if _isdir(data) else os.path.dirname(data)
            target = "/".join(prefix.split("/")[0:i])
            yield path, target
        yield data, prefix

        # Loop on file and directory from data
        if _isdir(data):
            for root, dirs, files in os.walk(data, followlinks=False):
                for name in files + dirs:
                    path = os.path.join(root, name)
                    target = os.path.join(prefix + root[len(data) :], name)
                    yield path, target

    # Loop on staging folder to include changelog and link.
    for root, dirs, files in os.walk(staging_dir, followlinks=False):
        for name in files + dirs:
            path = os.path.join(root, name)
            target = os.path.join("." + root[len(staging_dir) :], name)
            yield path, target


def _data_tar(build_dir, **kwargs):
    """
    Create data.tar.gz
    """
    # Create archive.
    filename = os.path.join(build_dir, "data.tar.gz")
    with tarfile.open(filename, "w:gz", format=tarfile.GNU_FORMAT) as f:
        for path, target in _walk(**kwargs):
            f.add(path, arcname=target, recursive=False, filter=_filter(mask=0o755))
    return filename


def _archive_deb(**kwargs):

    filename = os.path.join(kwargs["build_dir"], _template(kwargs["deb"], **kwargs))
    f = unix_ar.open(filename, "w")
    # debian-binary
    f.add(_debian_binary(**kwargs), unix_ar.ArInfo("debian-binary", gid=0, uid=0, perms=0o100644))

    # Generate change log
    _write_changelog(**kwargs)
    # Generate symlinks
    _write_symlink(**kwargs)

    # control.tar.gz
    f.add(_control_tar(**kwargs), unix_ar.ArInfo("control.tar.gz", gid=0, uid=0, perms=0o100644))

    # data.tar.gz
    f.add(_data_tar(**kwargs), unix_ar.ArInfo("data.tar.gz", gid=0, uid=0, perms=0o100644))

    f.close()

    return filename


def debbuild(
    name,
    data_src,
    build_dir=DEFAULT_BUILD_DIR,
    version=DEFAULT_VERSION,
    deb=DEFAULT_DEB,
    description="",
    long_description="",
    preinst=None,
    postinst=None,
    prerm=None,
    postrm=None,
    architecture=DEFAULT_ARCHITECTURE,
    distribution=DEFAULT_DISTRIBUTION,
    source_date=None,
    url=None,
    maintainer=DEFAULT_MAINTAINER,
    output=None,
    symlink=None,
    depends=[],
):
    if source_date is None:
        source_date = datetime.datetime.now(datetime.timezone.utc)

    cwd = os.getcwd()
    if output is None:
        output = cwd
    # To simplify the building process, let switch to staging folder.
    os.makedirs(build_dir, exist_ok=True)

    # Clear staging
    staging_dir = os.path.join(build_dir, STAGING_DIR)
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)

    # Create the debian archive
    filename = _archive_deb(
        build_dir=build_dir,
        staging_dir=staging_dir,
        name=name,
        version=version,
        deb=deb,
        data_src=data_src,
        description=description,
        long_description=long_description,
        preinst=preinst,
        postinst=postinst,
        prerm=prerm,
        postrm=postrm,
        architecture=architecture,
        distribution=distribution,
        source_date=source_date,
        maintainer=maintainer,
        url=url,
        symlink=symlink,
        depends=depends,
    )
    # Move the archive to output folder.
    shutil.move(filename, os.path.join(output, os.path.basename(filename)))
