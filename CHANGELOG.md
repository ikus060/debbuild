# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.4.0b3](https://gitlab.com/ikus-soft/debbuild/tags/0.4.0b3) - 2026-08-21

<small>[Compare with 0.4.0b2](https://gitlab.com/ikus-soft/debbuild/compare/0.4.0b2...0.4.0b3)</small>

### Misc

- debbuild: rename changelog.gz to changelog.Debian.gz per Debian policy ([cb3dd3a](https://gitlab.com/ikus-soft/debbuild/commit/cb3dd3a66b75f10d834f4ea372cdd60e6034a115) by Patrik Dufresne).

## [0.4.0b2](https://gitlab.com/ikus-soft/debbuild/tags/0.4.0b2) - 2026-08-21

<small>[Compare with 0.4.0b1](https://gitlab.com/ikus-soft/debbuild/compare/0.4.0b1...0.4.0b2)</small>

### Misc

- ci: upload all tags to pypi ([172e11e](https://gitlab.com/ikus-soft/debbuild/commit/172e11ec86033a48fd310a5b863fa760784aee0b) by Patrik Dufresne).
- debbuild: detect host architecture by default instead of hardcoded value ([917012a](https://gitlab.com/ikus-soft/debbuild/commit/917012a4acc1a68b4da9edb1af651f3ae47b4901) by Patrik Dufresne).

## [0.4.0b1](https://gitlab.com/ikus-soft/debbuild/tags/0.4.0b1) - 2026-08-21

<small>[Compare with 0.3.0](https://gitlab.com/ikus-soft/debbuild/compare/0.3.0...0.4.0b1)</small>

### Added

- ci: add python build matrix ([9939487](https://gitlab.com/ikus-soft/debbuild/commit/9939487fb8bcc8933b4ecf87b071067a20ee967d) by Patrik Dufresne).
- debbuild: add copyright file generation with license support ([fb2c439](https://gitlab.com/ikus-soft/debbuild/commit/fb2c4393e7a18918f865a7a1d335de1a7aeb3a0a) by Patrik Dufresne).
- test: add lintian test ([e035251](https://gitlab.com/ikus-soft/debbuild/commit/e035251abd1dee96baf2418d7b17b7f3da6e9cfd) by Patrik Dufresne).

### Removed

- debuild: remove usage of follow_symlinks ([c31bcae](https://gitlab.com/ikus-soft/debbuild/commit/c31bcaec587896089a2acca609866a835d9b76fb) by Patrik Dufresne).

### Misc

- debbuild: migrate os/stat usage to pathlib ([b81e33e](https://gitlab.com/ikus-soft/debbuild/commit/b81e33e7ec4f9cd97afef167fb1b19957b67cf17) by Patrik Dufresne).
- meta: update project copyright header ([c4be422](https://gitlab.com/ikus-soft/debbuild/commit/c4be422f207e48ebb3a5b1337bf6cca598dc8c01) by Patrik Dufresne).

## [0.3.0](https://gitlab.com/ikus-soft/debbuild/tags/0.3.0) - 2026-08-20

<small>[Compare with 0.2.2](https://gitlab.com/ikus-soft/debbuild/compare/0.2.2...0.3.0)</small>

### Added

- debbuild: add support for custom changelog file ([f4f70e8](https://gitlab.com/ikus-soft/debbuild/commit/f4f70e80fb299e9c63ee593f9b9747626114494a) by Patrik Dufresne).
- build: add changelog and release tox environments ([7714733](https://gitlab.com/ikus-soft/debbuild/commit/77147333ca58db7a0d0c055a8e28b7f762ae098a) by Patrik Dufresne).
- build: add isort config to pyproject.toml ([8b3956b](https://gitlab.com/ikus-soft/debbuild/commit/8b3956b71a064d83c8639bc3574a6aaedbc816af) by Patrik Dufresne).

### Merged

- ci: merge lint tox environments into single lint target ([517ea11](https://gitlab.com/ikus-soft/debbuild/commit/517ea1137b97e2563145a5d4ed9f1a3d4259f728) by Patrik Dufresne).

## [0.2.2](https://gitlab.com/ikus-soft/debbuild/tags/0.2.2) - 2025-06-18

<small>[Compare with 0.2.1](https://gitlab.com/ikus-soft/debbuild/compare/0.2.1...0.2.2)</small>

### Added

- Add support for config files ([e4c65b5](https://gitlab.com/ikus-soft/debbuild/commit/e4c65b54bb898bb313aa20f989628b487e272898) by Patrik Dufresne).

## [0.2.1](https://gitlab.com/ikus-soft/debbuild/tags/0.2.1) - 2025-03-14

<small>[Compare with 0.2.0](https://gitlab.com/ikus-soft/debbuild/compare/0.2.0...0.2.1)</small>

### Fixed

- Fix setuptools-scm dynamic version ([ae94196](https://gitlab.com/ikus-soft/debbuild/commit/ae94196f55a397a56d439e0f880645a43fc5b0e4) by Patrik Dufresne).

## [0.2.0](https://gitlab.com/ikus-soft/debbuild/tags/0.2.0) - 2025-03-14

<small>[Compare with 0.1.0](https://gitlab.com/ikus-soft/debbuild/compare/0.1.0...0.2.0)</small>

### Added

- Add test coverage for argument parsing ([b6beeae](https://gitlab.com/ikus-soft/debbuild/commit/b6beeae7f991e79888aedc041737d03f7c734808) by Patrik Dufresne).
- Add support for recommends, suggests, conflicts, provides, breaks ([7c2ce48](https://gitlab.com/ikus-soft/debbuild/commit/7c2ce4891e345b73573a652afd77e499b3b8f42f) by Patrik Dufresne).

### Fixed

- Fix wheel upload ([bf65a0f](https://gitlab.com/ikus-soft/debbuild/commit/bf65a0f4ad3132354e36cca9a9a7a060fded59a3) by Patrik Dufresne).

### Merged

- Merge branch 'patrik-copyright-year' into 'main' ([eacc765](https://gitlab.com/ikus-soft/debbuild/commit/eacc7653972e3be820734f6c3b750c22d9f0a4d7) by Patrik Dufresne).

### Misc

- Replace setup.cfg by pyproject.toml ([ecf4f4a](https://gitlab.com/ikus-soft/debbuild/commit/ecf4f4aa37f34690eabd34c35aa5bb4107288b6e) by Patrik Dufresne).
- Update Copyright Year ([2bab5a5](https://gitlab.com/ikus-soft/debbuild/commit/2bab5a5c253af05f39487063dfbc48f99240a56b) by Patrik Dufresne).

## [0.1.0](https://gitlab.com/ikus-soft/debbuild/tags/0.1.0) - 2023-02-01

<small>[Compare with 0.1.0b1](https://gitlab.com/ikus-soft/debbuild/compare/0.1.0b1...0.1.0)</small>

### Fixed

- Fix pipeline badge ([9ccb52e](https://gitlab.com/ikus-soft/debbuild/commit/9ccb52e4415c5ed29640b9546de2df81c65fda70) by Patrik Dufresne).

## [0.1.0b1](https://gitlab.com/ikus-soft/debbuild/tags/0.1.0b1) - 2023-02-01

<small>[Compare with first commit](https://gitlab.com/ikus-soft/debbuild/compare/58bf96c2c9c3193f417506013364241f598b9ca5...0.1.0b1)</small>

### Merged

- Merge branch 'patrik-first-version' into 'main' ([0756d3b](https://gitlab.com/ikus-soft/debbuild/commit/0756d3bee9b179fe780848db20539fbca2588399) by Patrik Dufresne).

### Misc

- Initial version ([58bf96c](https://gitlab.com/ikus-soft/debbuild/commit/58bf96c2c9c3193f417506013364241f598b9ca5) by Patrik Dufresne).
- Initial commit ([2e924a9](https://gitlab.com/ikus-soft/debbuild/commit/2e924a92d6bc1fc5984f8c0f46dac580240d3823) by Patrik Dufresne).
