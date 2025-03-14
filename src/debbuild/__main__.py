# -*- coding: utf-8 -*-
# Debbuild
#
# Copyright (C) 2025 IKUS Software. All rights reserved.
# IKUS Software inc. PROPRIETARY/CONFIDENTIAL.
# Use is subject to license terms.
#
from . import _config, debbuild


def main():
    cfg = _config()
    debbuild(
        name=cfg.name,
        description=cfg.description,
        long_description=cfg.long_description,
        version=cfg.version,
        deb=cfg.deb,
        data_src=cfg.data_src,
        preinst=cfg.preinst,
        postinst=cfg.postinst,
        prerm=cfg.prerm,
        postrm=cfg.postrm,
        architecture=cfg.architecture,
        distribution=cfg.distribution,
        url=cfg.url,
        maintainer=cfg.maintainer,
        output=cfg.output,
        symlink=cfg.symlink,
        depends=cfg.depends,
        recommends=cfg.recommends,
        suggests=cfg.suggests,
        conflicts=cfg.conflicts,
        provides=cfg.provides,
        breaks=cfg.breaks,
    )


if __name__ == "__main__":
    main()
