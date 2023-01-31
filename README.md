<p align="center">
<a href="LICENSE"><img alt="License" src="https://img.shields.io/pypi/l/debbuild"></a>
<a href="https://gitlab.com/ikus-soft/debbuild/pipelines"><img alt="Build" src="https://gitlab.com/ikus-soft/debbuild/badges/master/pipeline.svg"></a>
<a href="https://sonar.ikus-soft.com/dashboard?id=debbuild"><img alt="Quality Gate Minarca Client" src="https://sonar.ikus-soft.com/api/project_badges/measure?project=debbuild&metric=alert_status"></a>
<a href="https://sonar.ikus-soft.com/dashboard?id=debbuild"><img alt="Coverage" src="https://sonar.ikus-soft.com/api/project_badges/measure?project=debbuild&metric=coverage"></a>
</p>

# Debbuild

Command line utility to build Deb package without Debian.

## Description

This project allows to create archives for Debian (.deb) using only Python technologies. It is inspired by the [Fpm project](https://fpm.readthedocs.io/) which allows to create different types of archives on any platform.

I decided to create the Debbuild project, because it is a better way to create a Debian package on any platform. Previsouly, creating packages for Debian required the creation of a `debian` directory, the creation of several configuration files and tools like `dpkg` to build the package. With Debbuild it is possible to build the package without Debian by using a python script. This makes the creation of packages easier and the process simpler and more understandable.

A good usage scenario is the creation of a package containing the binary version of your project created from [PyInstaller](https://pyinstaller.org/en/stable/).

## Installation

Install Debbuild from pypi.

```sh
pip install debbuild
```

## Usage

A simple example how to use Debbuild to quickly create a Debian package.

```sh
debbuild --name mypackage --version 1.0.1 --data-src <path-to-dir> --data-prefix /opt/mypackage
```

## Support

If you need help or experience problem while using Debuild, open a ticket in [Gitlab](https://gitlab.com/ikus-soft/debbuild/-/issues/new) or Github.

## Roadmap

More specialized feature could be added:

* Service Unit creation
* Support more compression type like `zstd`

## License

This project is release under the MIT License.
