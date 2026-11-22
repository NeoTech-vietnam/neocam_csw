"""Real local-Git tests of selection, data preservation and live override behavior."""
import importlib.util
from contextlib import redirect_stderr
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import yaml

SPEC = importlib.util.spec_from_file_location('workspace', Path(__file__).resolve().parents[1] / 'TOOLCONF/workspace.py')
workspace = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workspace)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='neocam-workspace-test-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.root = self.base / 'project'
        self.repo = self.base / 'wifi'
        self.root.mkdir()
        self.repo.mkdir()
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Workspace test')
        self.git('config', 'user.email', 'workspace-test@example.invalid')
        (self.repo / 'wifi.c').write_text('initial\n')
        self.commit()
        self.sha = self.git('rev-parse', 'HEAD')
        self.packages = {'WifiStack': {'repo': '../wifi', 'ref': self.sha, 'dest': 'WifiStack'}}
        self.write_manifest()
        self.env = patch.dict(os.environ, {'CI': ''})
        self.env.start()
        self.addCleanup(self.env.stop)
        # Unlink junctions before TemporaryDirectory's Windows cleanup can traverse them.
        self.addCleanup(self.unlink_live)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL, text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-m', 'test: record fixture')

    def write_manifest(self):
        (self.root / 'packages.yml').write_text(yaml.safe_dump({'packages': self.packages}))

    def unlink_live(self):
        path = self.root / 'WifiStack'
        if workspace.is_link(path):
            if path.is_symlink():
                path.unlink()
            else:
                os.rmdir(path)

    def test_pin_repeat_branch_update_and_selection(self):
        workspace.fetch(self.root)
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'initial\n')
        modified = (self.root / 'WifiStack/wifi.c').stat().st_mtime_ns
        self.assertEqual(workspace.fetch(self.root)['WifiStack']['commit'], self.sha)
        self.assertEqual((self.root / 'WifiStack/wifi.c').stat().st_mtime_ns, modified)
        self.git('checkout', '-b', 'feature/wifi')
        (self.repo / 'wifi.c').write_text('branch\n')
        self.commit()
        second = self.git('rev-parse', 'HEAD')
        result = workspace.fetch(self.root, ref_override='WifiStack=feature/wifi')
        self.assertEqual(result['WifiStack']['commit'], second)
        self.assertTrue(workspace.status(self.root)['WifiStack']['selection_changed'])
        workspace.fetch(self.root)
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'initial\n')
        self.assertFalse((self.root / 'WifiStack/.git').exists())

    def test_live_edits_and_return_to_snapshot_preserve_checkout(self):
        override = self.root / 'packages.local.yml'
        override.write_text('overrides:\n  WifiStack:\n    path: ../wifi\n')
        workspace.fetch(self.root, override)
        self.assertTrue(workspace.is_link(self.root / 'WifiStack'))
        (self.repo / 'wifi.c').write_text('uncommitted local development\n')
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'uncommitted local development\n')
        self.assertEqual(workspace.status(self.root)['WifiStack']['status'], 'local-dirty')
        workspace.fetch(self.root)
        self.assertFalse(workspace.is_link(self.root / 'WifiStack'))
        self.assertEqual((self.repo / 'wifi.c').read_text(), 'uncommitted local development\n')
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'initial\n')
        self.assertFalse((self.repo / '.gitignore').exists())

    def test_modified_snapshot_and_unmanaged_folder_are_preserved(self):
        (self.root / 'WifiStack').mkdir()
        (self.root / 'WifiStack/mine.txt').write_text('keep')
        with self.assertRaises(workspace.WorkspaceError):
            workspace.fetch(self.root)
        (self.root / 'WifiStack/mine.txt').unlink()
        (self.root / 'WifiStack').rmdir()
        workspace.fetch(self.root)
        (self.root / 'WifiStack/wifi.c').write_text('keep edits')
        with self.assertRaises(workspace.WorkspaceError):
            workspace.fetch(self.root)
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'keep edits')

    def test_missing_ref_preflight_does_not_replace_existing_snapshot(self):
        workspace.fetch(self.root)
        with self.assertRaises(workspace.WorkspaceError):
            workspace.fetch(self.root, ref_override='WifiStack=missing-branch')
        self.assertEqual((self.root / 'WifiStack/wifi.c').read_text(), 'initial\n')

    def test_invalid_paths_case_collisions_and_overlaps(self):
        for dest in ['../outside', '/absolute', 'Conf', '.git', 'WifiStack/../outside', 'D:/bad', 'bad\\path']:
            with self.subTest(dest=dest):
                self.packages['WifiStack']['dest'] = dest
                self.write_manifest()
                with self.assertRaises(workspace.WorkspaceError):
                    workspace.fetch(self.root)
        self.packages['WifiStack']['dest'] = 'WifiStack'
        for dest in ['wifistack', 'WifiStack/nested']:
            self.packages['Other'] = {'repo': '../wifi', 'ref': self.sha, 'dest': dest}
            self.write_manifest()
            with self.assertRaises(workspace.WorkspaceError):
                workspace.fetch(self.root)

    def test_ci_and_conflicting_overrides_are_rejected(self):
        override = self.root / 'packages.local.yml'
        override.write_text('overrides:\n  WifiStack:\n    path: ../wifi\n')
        with patch.dict(os.environ, {'CI': 'true'}), self.assertRaises(workspace.WorkspaceError):
            workspace.fetch(self.root, override)
        with self.assertRaises(workspace.WorkspaceError):
            workspace.fetch(self.root, override, 'WifiStack=main')

    def test_archive_path_traversal_and_links_are_rejected(self):
        for name, kind in [('../outside', tarfile.REGTYPE), ('safe-link', tarfile.SYMTYPE),
                           ('C:/outside', tarfile.REGTYPE), ('.git/config', tarfile.REGTYPE)]:
            stream = io.BytesIO()
            with tarfile.open(fileobj=stream, mode='w') as archive:
                item = tarfile.TarInfo(name)
                item.type = kind
                archive.addfile(item)
            with self.assertRaises(workspace.WorkspaceError):
                workspace.extract_snapshot(stream.getvalue(), self.root / 'archive')

    def test_manifest_relocation_cleans_only_owned_old_destination(self):
        workspace.fetch(self.root)
        self.packages['WifiStack']['dest'] = 'NewWifi'
        self.write_manifest()
        workspace.fetch(self.root)
        self.assertFalse((self.root / 'WifiStack').exists())
        self.assertEqual((self.root / 'NewWifi/wifi.c').read_text(), 'initial\n')
        report = json.loads((self.root / '_out/packages-resolved.json').read_text())
        self.assertEqual(report['packages']['WifiStack']['commit'], self.sha)


class GitProxyRetryTests(unittest.TestCase):
    def test_proxy_dns_failure_retries_fetch_once_without_proxy(self):
        failed = subprocess.CompletedProcess([], 128, '', 'fatal: Could not resolve proxy: invalid.example')
        success = subprocess.CompletedProcess([], 0, 'fetched\n', '')
        output = io.StringIO()
        arguments = ('fetch', '--no-tags', '--', 'https://github.com/NeoTech-vietnam/WifiStack.git', 'tag')
        with patch.object(workspace.subprocess, 'run', side_effect=[failed, success]) as run, redirect_stderr(output):
            self.assertEqual(workspace.git(Path('cache'), *arguments), 'fetched')
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[0].args[0], ['git', '-C', 'cache', *arguments])
        self.assertEqual(run.call_args_list[1].args[0], ['git', '-c', 'http.proxy=', '-C', 'cache', *arguments])
        self.assertIn('proxy', output.getvalue().lower())

    def test_other_errors_and_non_fetch_commands_are_not_retried(self):
        for command, message in [('fetch', 'Authentication failed'),
                                 ('fetch', "couldn't find remote ref tag"),
                                 ('rev-parse', 'Could not resolve proxy')]:
            with self.subTest(command=command, message=message):
                result = subprocess.CompletedProcess([], 128, '', message)
                with patch.object(workspace.subprocess, 'run', return_value=result) as run:
                    with self.assertRaises(workspace.WorkspaceError):
                        workspace.git(Path('cache'), command)
                self.assertEqual(run.call_count, 1)

    def test_failed_direct_retry_stops_and_does_not_expose_credentials(self):
        failures = [subprocess.CompletedProcess([], 128, '', 'Could not resolve proxy: secret-value'),
                    subprocess.CompletedProcess([], 128, '', 'https://user:secret-value@example.invalid failed')]
        output = io.StringIO()
        with patch.object(workspace.subprocess, 'run', side_effect=failures) as run, redirect_stderr(output):
            with self.assertRaises(workspace.WorkspaceError) as caught:
                workspace.git(Path('cache'), 'fetch')
        self.assertEqual(run.call_count, 2)
        self.assertNotIn('secret-value', str(caught.exception) + output.getvalue())


if __name__ == '__main__':
    unittest.main()
