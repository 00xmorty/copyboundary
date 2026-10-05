import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'copyboundary'
loader = importlib.machinery.SourceFileLoader('cb', str(SCRIPT))
spec = importlib.util.spec_from_loader('cb', loader)
cb = importlib.util.module_from_spec(spec)
loader.exec_module(cb)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name).resolve()
        self.root = self.base / 'project'
        self.root.mkdir()

    def test_clean(self):
        (self.root / 'file').write_text('example')
        self.assertEqual(cb.scan(self.root)['status'], 'NO_FLAGGED_RISK')

    def test_external_file_not_read(self):
        target = self.base / 'outside'
        target.write_text('PRIVATE-SENTINEL')
        (self.root / 'link').symlink_to(target)
        report = cb.scan(self.root)
        self.assertEqual(report['status'], 'REVIEW')
        self.assertEqual(report['findings'][0]['scope'], 'external')
        self.assertNotIn('PRIVATE-SENTINEL', json.dumps(report))
        self.assertNotIn(str(self.base), json.dumps(report))
        self.assertEqual(target.read_text(), 'PRIVATE-SENTINEL')

    def test_internal_directory_not_followed(self):
        folder = self.root / 'folder'
        folder.mkdir()
        (folder / 'file').write_text('example')
        (self.root / 'alias').symlink_to(folder, target_is_directory=True)
        report = cb.scan(self.root)
        self.assertEqual(report['visited'], 3)
        self.assertEqual(report['findings'][0]['scope'], 'internal')

    def test_external_directory_not_followed(self):
        folder = self.base / 'outside'
        folder.mkdir()
        (folder / 'secret-name').write_text('example')
        (self.root / 'alias').symlink_to(folder, target_is_directory=True)
        report = cb.scan(self.root)
        self.assertEqual(report['visited'], 1)
        self.assertNotIn('secret-name', json.dumps(report))

    def test_broken(self):
        (self.root / 'broken').symlink_to('missing')
        self.assertEqual(cb.scan(self.root)['findings'][0]['target_state'], 'broken')

    def test_cycle(self):
        (self.root / 'a').symlink_to('b')
        (self.root / 'b').symlink_to('a')
        self.assertEqual(cb.scan(self.root)['status'], 'UNKNOWN')

    def test_chain_crosses_boundary(self):
        (self.root / 'a').symlink_to('b')
        (self.root / 'b').symlink_to(self.base / 'missing')
        self.assertTrue(all(x['scope'] == 'external' for x in cb.scan(self.root)['findings']))

    def test_fifo_not_opened(self):
        os.mkfifo(self.root / 'pipe')
        self.assertEqual(cb.scan(self.root)['findings'][0]['type'], 'fifo')

    def test_permission_failure(self):
        with patch.object(cb.os, 'scandir', side_effect=PermissionError):
            self.assertEqual(cb.scan(self.root)['status'], 'UNKNOWN')

    def test_limit(self):
        for name in ['a', 'b']:
            (self.root / name).touch()
        self.assertEqual(cb.scan(self.root, 1)['status'], 'UNKNOWN')

    def test_root_symlink(self):
        alias = self.base / 'alias'
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            cb.scan(alias)

    def test_cli_missing(self):
        result = subprocess.run(['python3', str(SCRIPT), str(self.base / 'missing'), '--json'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertNotIn(str(self.base), result.stdout + result.stderr)

    def test_cli_escapes_control_characters(self):
        (self.root / 'bad\nname').symlink_to('missing')
        result = subprocess.run(['python3', str(SCRIPT), str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('bad\\nname', result.stdout)


if __name__ == '__main__':
    unittest.main()
