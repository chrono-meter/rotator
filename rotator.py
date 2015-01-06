#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rotate file or directory.
"""
import sys
import logging
import argparse
from pathlib import Path
import shutil
import re
import collections

__all__ = ()
__version__ = '1.0.0'
__author__ = __author_email__ = 'chrono-meter@gmx.net'
__license__ = 'PSF'
__url__ = 'https://github.com/chrono-meter/rotator'
# http://pypi.python.org/pypi?%3Aaction=list_classifiers
__classifiers__ = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: Python Software Foundation License',
    'Operating System :: OS Independent',
    'Topic :: System :: Archiving',
    'Topic :: System :: Filesystems',
    'Topic :: Utilities',
]

logger = logging.getLogger(__name__)


def verbose_to_loglevel(verbose: int=0, default_level=logging.WARNING):
    assert isinstance(verbose, int)

    levels = [
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG,
        logging.NOTSET,
    ]

    try:
        return levels[levels.index(default_level) + verbose]
    except LookupError:
        return logging.NOTSET


class SurrogateNamespace(dict):

    def __init__(self, *accessibles):
        super().__init__()
        self.accessibles = accessibles

    def __getitem__(self, item):
        for accessible in self.accessibles:
            if isinstance(accessible, collections.Mapping):
                try:
                    return accessible[item]
                except LookupError:
                    pass
            else:
                try:
                    return getattr(accessible, item)
                except AttributeError:
                    pass
        raise KeyError(item)


def eval_template(string: str, *objects, **kwargs) -> str:
    from datetime import datetime, timedelta

    now = datetime.now()
    today = datetime.today()
    yesterday = today + timedelta(days=-1)
    tomorrow = today + timedelta(days=1)

    ns = SurrogateNamespace(*(objects + (kwargs, locals())))

    return re.sub(r'\{\{(.*?)\}\}', lambda m: str(eval(m.group(1), ns)), string)


class Rotator:

    def __call__(self, target: Path, *, format: str, copy: bool=False, dry_run: bool=False, max_gen: int=4):
        assert max_gen >= 1

        if not target.is_absolute():
            target = target.absolute()

        if not target.exists():
            raise FileNotFoundError('%s' % (target, ))

        names = []
        for gen in range(1, max_gen + 1):
            name = Path(eval_template(format, target, generation=gen))
            if not name.is_absolute():
                name = target.parent / name.name
            names.append(name)

        # rotate
        for name, rotated_name in zip(reversed(names), reversed(names[1:] + [None])):
            assert name
            logger.debug('try to rotate %s', name)

            if not name.exists():
                continue

            if rotated_name is not None:
                if not dry_run:
                    name.rename(rotated_name)
                logger.info('%s is moved as %s', name, rotated_name)
            else:
                if not dry_run:
                    if not name.is_dir():
                        name.unlink()
                    else:
                        shutil.rmtree(str(name))
                logger.info('%s is removed', name)

        # rename target or copy target
        name = target
        rotated_name = names[0]
        # TODO: truncate?
        if not copy:
            if not dry_run:
                name.rename(rotated_name)
            logger.info('%s is moved as %s', name, rotated_name)
        else:
            if not dry_run:
                if not name.is_dir():
                    shutil.copy2(str(name), str(rotated_name))
                else:
                    shutil.copytree(str(name), str(rotated_name))
            logger.info('%s is copied as %s', name, rotated_name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--verbose', '-v', action='count', default=0, help='increase verbosity levels')
    parser.add_argument('--dry-run', '-n', action='store_true', default=False, help='test mode')
    parser.add_argument('--copy', action='store_true', default=False, help='copy target instead of renaming')
    parser.add_argument('--max-gen', type=int, default=4)
    parser.add_argument('--format', type=str, default='{{name}}.{{generation}}')
    parser.add_argument('targets', nargs='+', type=Path)

    arg = parser.parse_args(argv)
    arg.verbose = verbose_to_loglevel(arg.verbose)
    logger.setLevel(arg.verbose)
    logger.debug('command line arguments: %s', arg)

    try:
        rotate = Rotator()
        for target in arg.targets:
            rotate(target, format=arg.format, copy=arg.copy, dry_run=arg.dry_run, max_gen=arg.max_gen)
    except:
        if arg.verbose >= logging.DEBUG:
            logger.debug('Unhandled exception', exc_info=True)
            return -1
        raise


if __name__ == '__main__':
    logging.basicConfig(format='%(message)s', stream=sys.stdout, level=logging.NOTSET)
    sys.exit(main() or 0)
