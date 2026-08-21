# debbuild: Pure-Python DEB package builder.
# Copyright (C) 2025-2026 Patrik Dufresne <patrik@ikus-soft.com>
#
# SPDX-License-Identifier: MIT

import argparse
import datetime
import gzip
import hashlib
import shutil
import tarfile
from email.utils import parseaddr
from pathlib import Path

import jinja2
import license
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

DEFAULT_LICENSE_NAME = "Undefined"

DEFAULT_LICENSE_TEXT = """License text not provided. Please define a license using --license-text
or --license-name option."""

TMPL_CONTROL = """Package: {{name}}
Version: {{version}}
Section: misc
Priority: optional
Architecture: {{architecture}}
Maintainer: {{maintainer}}
Homepage: {{ url }}
{% for key, items in [('Depends', depends), ('Recommends', recommends), ('Suggests', suggests), ('Conflicts', conflicts), ('Replaces', replaces), ('Provides', provides), ('Breaks', breaks)] -%}
{%- if items %}{{ key }}: {{ ', '.join(items) }}
{% endif -%}
{%- endfor -%}
Description: {{ description|replace("\n", " ") }}
{%- filter indent(width=1) %}
{{ long_description | replace("\n", " ") | wordwrap(78) }}
{% endfilter -%}
"""

TMPL_CHANGELOG = """{{name}} ({{version}}) {{distribution}}; urgency=medium

  * Package created with DebBuild.

 -- {{maintainer}}  {{source_date.strftime("%a, %d %b %Y %T %z")}}
"""

TMPL_COPYRIGHT = """Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: {{name}}
Upstream-Contact: {{maintainer}}
Source: {{url}}

Files: *
Copyright: {{copyright}}
License: {{license_name}}
{{license_text|replace('\n\n', '\n.\n')|indent(1, blank=True, first=True)}}
"""


class DebBuildException(Exception):
    pass


def _filter(mode=None, mask=None, uid=0, gid=0, uname="root", gname="root"):
    """
    Used to apply proper attributes to files archived.
    """

    def _filter(tarinfo):
        if mode is not None:
            tarinfo.mode = mode
        if mask is not None:
            tarinfo.mode = tarinfo.mode & mask
        tarinfo.uid = uid
        tarinfo.gid = gid
        tarinfo.gname = gname
        tarinfo.uname = uname
        return tarinfo

    return _filter


def _config(args=None):
    parser = argparse.ArgumentParser(
        prog="debbuild",
        description="Pure-Python DEB package builder",
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
        help="The directory to include in the package. This flag can be specified multiple times. Must be defined as <destination>=<path>. If your data is located in `./build/mypackage` and you want your application to be installed in `/opt/mypackage`, data should be defined as `--data-src /opt/mypackage=./build/mypackage`",
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
        help="A script to be run after package removal to purge remaining (config) files",
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
        help="Define a symlink to be created as `<link>=<target>`. This flag can be specified multiple times. e.g.: `--symlink /opt/mypackage/bin/mypackage=/usr/bin/mypackage`",
        action='append',
        type=str,
    )
    for key in ['depends', 'recommends', 'suggests', 'conflicts', 'replaces', 'provides', 'breaks']:
        parser.add_argument(
            f"--{key}",
            help=f"Define a new {key}",
            action='append',
            type=str,
            default=[],
        )
    parser.add_argument(
        "--config-file",
        help="Additional file to be marked as a configuration file (can be specified multiple times)",
        action='append',
        default=[],
        type=str,
    )
    parser.add_argument(
        "--changelog",
        help="Path to a custom Debian changelog file to be used instead of the auto-generated one. The file will be compressed and installed as /usr/share/doc/<name>/changelog.gz",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--copyright-file",
        help="Path to a copyright file to be used. The file will be installed as /usr/share/doc/<name>/copyright",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--copyright",
        help="Copyright holder(s). Default: current year + maintainer",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--license-name",
        help=f"License name (e.g., MIT, GPL-3.0, Apache-2.0). Default: {DEFAULT_LICENSE_NAME}",
        type=str,
        default=DEFAULT_LICENSE_NAME,
    )
    parser.add_argument(
        "--license-text",
        help="Custom license text file path.",
        type=str,
    )
    return parser.parse_args(args)


def _as_tuple(value, error_message):
    """
    Used to read --data-src and --symlink configuration that could be defined as string, list of string or list of tuple.
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
                except (ValueError, TypeError):
                    k, v = item.partition('=')[0::2]
            except (ValueError, TypeError):
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
    build_path = Path(build_dir)
    filename = build_path / "debian-binary"
    filename.write_text("2.0\n")
    return str(filename)


def _collect_conffiles(data_src, config_files, staging_dir):
    """
    Collect files considered as conffiles, based on default (/etc) and user-supplied list.
    Returns a list of relative paths (starting with /) to include in DEBIAN/conffiles
    """
    conffiles = set()
    for path, target in _walk(data_src=data_src, staging_dir=staging_dir):
        if (path.is_file() and not path.is_symlink()) and target.startswith("./etc/"):
            conffiles.add(target[1:])  # remove leading '.' to get absolute-like path

    # Add user-supplied files explicitly
    for custom in config_files:
        if not custom.startswith("/"):
            raise DebBuildException("Custom config file must start with '/': %s" % custom)
        conffiles.add(custom)

    return sorted(conffiles)


def _control_tar(build_dir, **kwargs):
    """
    Create control.tar.gz
    """
    build_path = Path(build_dir)
    filename = build_path / "control.tar.gz"

    with tarfile.open(str(filename), "w:gz", format=tarfile.GNU_FORMAT) as f:
        # Write control script
        f.add(_write_control(build_dir=build_dir, **kwargs), arcname="./control", filter=_filter(mode=0o644))

        # Write md5sum
        f.add(_write_control_md5sums(build_dir=build_dir, **kwargs), arcname="./md5sums", filter=_filter(mode=0o644))

        # Write conffiles if any
        conffiles = _collect_conffiles(kwargs["data_src"], kwargs.get("config_files") or [], kwargs["staging_dir"])
        if conffiles:
            conffile_path = build_path / "conffiles"
            conffile_path.write_text("\n".join(conffiles) + "\n")
            f.add(str(conffile_path), arcname="./conffiles", filter=_filter(mode=0o644))

        # Add post & pre scripts
        for script in ["preinst", "postinst", "prerm", "postrm"]:
            if not kwargs.get(script):
                continue
            path = kwargs[script]
            p = Path(path)
            if not p.is_file() or p.is_symlink():
                raise DebBuildException("%s script `%s` must be a file" % (script, path))
            f.add(path, arcname="./" + script, filter=_filter(mode=0o755))

    return str(filename)


def _write_control(build_dir, **kwargs):
    """
    Create a control file from template.
    """
    build_path = Path(build_dir)
    filename = build_path / "control"
    data = _template(TMPL_CONTROL, **kwargs)
    filename.write_text(data if data.endswith("\n") else data + "\n")
    return str(filename)


def _write_control_md5sums(build_dir, **kwargs):
    """
    Generate md5sum for all files.
    """
    build_path = Path(build_dir)
    filename = build_path / "md5sums"
    lines = []

    for path, target in _walk(**kwargs):
        if path.is_file() and not path.is_symlink():
            md5_value = hashlib.md5(path.read_bytes()).hexdigest()
            # md5hash + 2 spaces + filename without ./
            lines.append(f"{md5_value}  {target[2:]}")

    filename.write_text("\n".join(lines) + ("\n" if lines else ""))
    return str(filename)


def _write_changelog(name, staging_dir, changelog=None, **kwargs):
    """
    Create a changelog.gz. If a custom changelog file is provided, use its
    content instead of the auto-generated template.
    """
    staging_path = Path(staging_dir)
    filename = staging_path / f"usr/share/doc/{name}/changelog.gz"
    filename.parent.mkdir(parents=True, exist_ok=True)

    if changelog:
        p = Path(changelog)
        if not p.is_file() or p.is_symlink():
            raise DebBuildException("changelog `%s` must be a file" % changelog)
        with gzip.open(filename, "w") as f:
            f.write(p.read_bytes())
    else:
        content = _template(TMPL_CHANGELOG, name=name, **kwargs)
        with gzip.open(filename, "w") as f:
            f.write(content.encode("utf-8"))


def _write_copyright(
    name, staging_dir, maintainer, url, copyright_file, copyright, license_name, license_text, **kwargs
):
    """
    Create a copyright file in Debian DEP-5 format.
    If not provided, generates a default copyright file.
    """
    staging_path = Path(staging_dir)
    filename = staging_path / f"usr/share/doc/{name}/copyright"
    filename.parent.mkdir(parents=True, exist_ok=True)

    if copyright_file:
        p = Path(copyright_file)
        if not p.is_file() or p.is_symlink():
            raise DebBuildException("copyright-file `%s` must be a file" % copyright_file)
        filename.write_text(p.read_text())
        return

    # Default copyright year and holder
    year = datetime.datetime.now().year

    # Default
    if license_name == DEFAULT_LICENSE_NAME and license_text is None:
        license_text = DEFAULT_LICENSE_TEXT
    elif not license_text:
        maintainer_name, maintainer_email = parseaddr(maintainer, strict=False)
        try:
            license_text = license.find(license_name).render(year=year, name=maintainer_name, email=maintainer_email)
        except KeyError:
            pass

    content = _template(
        TMPL_COPYRIGHT,
        name=name,
        maintainer=maintainer,
        url=url,
        copyright=copyright or f"{year} {maintainer}",
        license_name=license_name,
        license_text=license_text or "",
    )
    filename.write_text(content if content.endswith("\n") else content + "\n")


def _write_symlink(symlink, staging_dir, **kwargs):
    """
    Create the symlink in staging folder.
    """
    # Loop on symlink
    for link, target in _as_tuple(symlink, 'expect symlink to be defined as <link>=<target>'):
        # Make the path relative
        link = Path(staging_dir) / link.strip('/')
        # Create missing directories
        link.parent.mkdir(parents=True, exist_ok=True)
        # Finally create the symlink.
        link.symlink_to(target)


def _walk(data_src, staging_dir, **kwargs):
    """
    Used to walk through the data directory by listing its content recursively.
    """
    # Loop on each data source
    for prefix, data in _as_tuple(data_src, 'expect `data-src` to be defined as <prefix>=<data>'):
        # Validate Path
        data_path = Path(data)
        if not (data_path.is_dir() or data_path.is_file()) or data_path.is_symlink():
            raise DebBuildException("data-src path `%s` must be a file or directory" % data)

        # Make sure prefix start with dot (.)
        if not prefix.startswith("."):
            prefix = ("." if prefix.startswith("/") else "./") + prefix

        # Yield intermediate directories
        prefix_parts = prefix.split("/")
        for i in range(1, len(prefix_parts)):
            path = data_path if data_path.is_dir() else data_path.parent
            target = "/".join(prefix_parts[0:i])
            yield path, target
        yield data_path, prefix

        # Loop on file and directory from data
        if data_path.is_dir():
            for path in data_path.rglob("*"):
                relative = path.relative_to(data_path)
                target = f"{prefix}/{relative}"
                yield path, target

    # Loop on staging folder to include changelog and link.
    staging_path = Path(staging_dir)
    if staging_path.exists():
        for path in staging_path.rglob("*"):
            relative_suffix = path.relative_to(staging_path)
            target = f"./{relative_suffix}"
            yield path, target


def _data_tar(build_dir, **kwargs):
    """
    Create data.tar.gz
    """
    build_path = Path(build_dir)
    filename = build_path / "data.tar.gz"
    with tarfile.open(str(filename), "w:gz", format=tarfile.GNU_FORMAT) as f:
        for path, target in _walk(**kwargs):
            f.add(str(path), arcname=target, recursive=False, filter=_filter(mask=0o755))
    return str(filename)


def _archive_deb(**kwargs):

    build_path = Path(kwargs["build_dir"])
    filename = build_path / _template(kwargs["deb"], **kwargs)
    f = unix_ar.open(filename, "w")
    # debian-binary
    f.add(_debian_binary(**kwargs), unix_ar.ArInfo("debian-binary", gid=0, uid=0, perms=0o100644))

    # Generate change log
    _write_changelog(**kwargs)
    # Generate copyright
    _write_copyright(**kwargs)
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
    recommends=[],
    suggests=[],
    conflicts=[],
    provides=[],
    breaks=[],
    config_files=[],
    changelog=None,
    copyright_file=None,
    copyright=None,
    license_name=DEFAULT_LICENSE_NAME,
    license_text=None,
):
    if source_date is None:
        source_date = datetime.datetime.now(datetime.timezone.utc)

    cwd = Path.cwd()
    output_path = Path(output) if output else cwd
    build_path = Path(build_dir)

    # Create build directory
    build_path.mkdir(exist_ok=True)

    # Clear staging
    staging_path = build_path / STAGING_DIR
    if staging_path.exists():
        shutil.rmtree(staging_path)
    staging_path.mkdir(parents=True, exist_ok=True)

    # Create the debian archive
    filename = _archive_deb(
        build_dir=str(build_path),
        staging_dir=str(staging_path),
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
        recommends=recommends,
        suggests=suggests,
        conflicts=conflicts,
        provides=provides,
        breaks=breaks,
        config_files=config_files,
        changelog=changelog,
        copyright_file=copyright_file,
        copyright=copyright,
        license_name=license_name,
        license_text=license_text,
    )
    # Move the archive to output folder.
    shutil.move(filename, output_path / filename.name)
