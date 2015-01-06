#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from cx_Freeze import setup, Executable


if __name__ == '__main__':
    import rotator as target
    setup(
        name=target.__name__,
        version=target.__version__,
        description=target.__doc__,
        executables=[
            Executable(target.__file__),
        ],
        options={
            'build_exe': {'include_msvcr': True},
        },
    )
