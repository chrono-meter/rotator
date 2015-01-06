#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import unittest
from pathlib import Path
import sys
import subprocess
import tempfile


def run(*args, **kwargs):
    args = [
        sys.executable,
        str(Path(__file__).parent.parent / 'rotator.py'),
        # '-vvv',
    ] + [str(i) for i in args]
    return subprocess.check_call(args, shell=False, stdout=sys.stdout, stderr=subprocess.STDOUT, **kwargs)


class Test(unittest.TestCase):

    def _test_rotate(self, name='test', max_gen=3, copy=False, setup=Path.touch):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            target = tmp / name

            for i in range(max_gen * 2):
                setup(target)

                self.assertEqual(len(list(tmp.iterdir())), min(i + 1, max_gen + 1))

                if not copy:
                    run('--max-gen', max_gen, target)
                    self.assertFalse(target.exists())
                else:
                    run('--max-gen', max_gen, '--copy', target)
                    self.assertTrue(target.exists())

                self.assertEqual(len(list(tmp.iterdir())), min(i + 1, max_gen) + int(copy))

    def test_file(self):
        self._test_rotate()

    def test_copy_file(self):
        self._test_rotate(copy=True)

    def test_directory(self):
        self._test_rotate(setup=Path.mkdir)

    def test_copy_directory(self):
        def mkdir(path: Path):
            if not path.exists():
                path.mkdir()
        self._test_rotate(setup=mkdir, copy=True)
