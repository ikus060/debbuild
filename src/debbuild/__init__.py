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
Depends:
Maintainer: {{maintainer}}
Description: {{ description|replace("\n", " ") }}
{%- filter indent(width=1) %}
{{ long_description }}
{% endfilter -%}
Homepage: {{ url }}
"""

TMPL_CHANGELOG = """{{name}} ({{version}}) {{distribution}}; urgency=medium

  * Package created with DebBuild.

 -- {{maintainer}}  {{source_date.strftime("%a, %d %b %Y %T %z")}}
"""


class DebBuildException(Exception):
    pass


def _filter(mode=None, mask=None, uid=0, gui=0, uname="root", gname="root"):
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
        "--deb",
        help="The debian package to be generated. Default to `<name>_<version>_all.deb` (not required)",
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
        help="The directory to include in the package.",
        required=True,
        type=str,
    )
    parser.add_argument(
        "--data-prefix",
        help="Add this prefix to the files",
        default=".",
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

    return parser.parse_args()


def _template(tmpl, **kwargs):
    t = jinja2.Environment().from_string(tmpl)
    return t.render(**kwargs)


def _debian_binary(version="2.0"):
    """
    debian-binary contains the version.
    """
    with open("debian-binary", "w") as f:
        f.write(version)
        f.write("\n")


def _control_tar(**kwargs):
    """
    Create control.tar.gz
    """
    f = tarfile.open("control.tar.gz", "w:gz", format=tarfile.GNU_FORMAT)

    # Write control script
    _write_control(**kwargs)
    f.add("./control", filter=_filter(mode=0o644))

    # Add post & pre scripts
    for script in ["preinst", "postinst", "prerm", "postrm"]:
        if not kwargs.get(script, None):
            continue
        path = kwargs[script]
        if not os.path.isfile(path):
            raise DebBuildException("%s script `%s` must be a file" % (script, path))
        f.add(path, arcname="./" + script, filter=_filter(mode=0o755))

    # Close archive to flush data on disk.
    f.close()


def _write_control(**kwargs):
    """
    Create a control file from template.
    """
    with open("control", "w") as c:
        data = _template(TMPL_CONTROL, **kwargs)
        c.write(data)
        # Write required final newline
        if not data.endswith("\n"):
            c.write("\n")


def _write_control_md5sums(**kwargs):
    """
    Generate md5sum for all files.
    """
    first = True
    with open("md5sums", "w") as f:
        for path, target in _walk(**kwargs):
            if not os.path.isfile(path):
                continue
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


def _write_changelog(name, **kwargs):
    """
    Create a changelog.gz
    """
    filename = f"staging/usr/share/doc/{name}/changelog.gz"
    os.makedirs(os.path.dirname(filename))
    with gzip.open(filename, "w") as f:
        f.write(_template(TMPL_CHANGELOG, name=name, **kwargs).encode("utf-8"))


def _walk(data_src, data_prefix, **kwargs):
    """
    Used to walk trought the data directory by listing it's content recursively.
    """
    # Validate Path
    if not os.path.isdir(data_src):
        raise DebBuildException("data-src path `%s` is not a directory")

    # Make sure prefix start with dot (.)
    if not data_prefix.startswith("."):
        data_prefix = ("." if data_prefix.startswith("/") else "./") + data_prefix

    # Yield prefix
    for i in list(range(1, 1 + len(data_prefix.split("/")))):
        yield data_src, "/".join(data_prefix.split("/")[0:i])

    # Loop on file and directory from data_src
    for root, dirs, files in os.walk(data_src, followlinks=False):
        for name in files + dirs:
            path = os.path.join(root, name)
            target = os.path.join(data_prefix + root[len(data_src) :], name)
            yield path, target

    # Loop on staging folder to include changelog and link.
    for root, dirs, files in os.walk(STAGING_DIR, followlinks=False):
        for name in files + dirs:
            path = os.path.join(root, name)
            target = os.path.join("." + root[len(STAGING_DIR) :], name)
            yield path, target


def _data_tar(**kwargs):
    """
    Create data.tar.gz
    """
    # Create archive.
    with tarfile.open("data.tar.gz", "w:gz", format=tarfile.GNU_FORMAT) as f:
        for path, target in _walk(**kwargs):
            f.add(path, arcname=target, recursive=False, filter=_filter(mask=0o755))


def _archive_deb(**kwargs):

    filename = _template(kwargs["deb"], **kwargs)
    f = unix_ar.open(filename, "w")
    # debian-binary
    _debian_binary()
    f.addfile(unix_ar.ArInfo("debian-binary", gid=0, uid=0, perms=0o100644))

    # Generate change log
    _write_changelog(**kwargs)

    # control.tar
    _control_tar(**kwargs)
    f.addfile(unix_ar.ArInfo("control.tar.gz", gid=0, uid=0, perms=0o100644))

    # data.tar
    _data_tar(**kwargs)
    f.addfile(unix_ar.ArInfo("data.tar.gz", gid=0, uid=0, perms=0o100644))

    f.close()


def debbuild(
    name,
    data_src,
    build_dir=DEFAULT_BUILD_DIR,
    version=DEFAULT_VERSION,
    deb=DEFAULT_DEB,
    description="",
    long_description="",
    data_prefix="",
    preinst=None,
    postinst=None,
    prerm=None,
    postrm=None,
    architecture=DEFAULT_ARCHITECTURE,
    distribution=DEFAULT_DISTRIBUTION,
    source_date=None,
    url=None,
    maintainer=DEFAULT_MAINTAINER,
):
    if source_date is None:
        source_date = datetime.datetime.now(datetime.timezone.utc)
    cwd = os.getcwd()
    try:
        os.makedirs(build_dir, exist_ok=True)
        os.chdir(build_dir)
        shutil.rmtree(STAGING_DIR)
        _archive_deb(
            name=name,
            version=version,
            deb=deb,
            data_src=data_src,
            description=description,
            long_description=long_description,
            data_prefix=data_prefix,
            preinst=preinst,
            postinst=postinst,
            prerm=prerm,
            postrm=postrm,
            architecture=architecture,
            distribution=distribution,
            source_date=source_date,
            maintainer=maintainer,
            url=url,
        )
    finally:
        os.chdir(cwd)
