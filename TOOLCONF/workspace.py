#!/usr/bin/env python3
"""Assemble pinned Git snapshots or explicit live development checkouts."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESERVED = {'conf', 'gconf', 'toolconf', 'test', 'docs', '_metadata', '.github',
            '.git', '.workspace', '_out', '_build', 'managed_components'}


class WorkspaceError(RuntimeError):
    pass


def git(directory, *arguments, binary=False):
    command = ['git', '-C', str(directory), *arguments]
    result = subprocess.run(command, capture_output=True, text=not binary)
    retried_direct = False
    diagnostic = result.stderr or ''
    if isinstance(diagnostic, bytes):
        diagnostic = diagnostic.decode('utf-8', errors='replace')
    if result.returncode and arguments[0] == 'fetch' and 'could not resolve proxy' in diagnostic.lower():
        print('workspace: configured Git proxy could not be resolved; retrying this fetch with http.proxy=.',
              file=sys.stderr)
        result = subprocess.run(['git', '-c', 'http.proxy=', *command[1:]],
                                capture_output=True, text=not binary)
        retried_direct = True
    if result.returncode:
        # Repository URLs can contain credentials; do not echo the command or stderr.
        retry = ' after retrying without proxy' if retried_direct else ''
        raise WorkspaceError(f'Git {arguments[0]} failed{retry}; check repository access and revision.')
    return result.stdout if binary else result.stdout.strip()


def load_yaml(path):
    try:
        document = yaml.safe_load(path.read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        raise WorkspaceError(f'Cannot read YAML file {path.name}.') from exc
    if not isinstance(document, dict):
        raise WorkspaceError(f'{path.name} must contain a mapping.')
    return document


def is_link(path):
    return path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction())


def exists(path):
    return os.path.lexists(path)


def destination(root, value):
    if not isinstance(value, str) or not value or '\\' in value or ':' in value:
        raise WorkspaceError('Destination must be a relative forward-slash path.')
    parts = PurePosixPath(value).parts
    if (PurePosixPath(value).is_absolute() or not parts or
            any(p in {'.', '..'} or p.startswith('.') or p.endswith((' ', '.')) for p in parts) or
            parts[0].casefold() in RESERVED or any(':' in p for p in parts)):
        raise WorkspaceError(f'Invalid or reserved destination: {value}')
    # Never traverse a link in a destination parent.
    target = root
    for part in parts[:-1]:
        target = target / part
        if is_link(target):
            raise WorkspaceError('Destination parent is a link.')
    return root.joinpath(*parts)


def manifest(root):
    packages = load_yaml(root / 'packages.yml').get('packages')
    if not isinstance(packages, dict) or not packages:
        raise WorkspaceError('packages.yml requires a nonempty packages mapping.')
    destinations = []
    for name, package in packages.items():
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', name):
            raise WorkspaceError('Invalid package name.')
        if not isinstance(package, dict) or set(package) != {'repo', 'ref', 'dest'}:
            raise WorkspaceError(f'{name}: expected repo, ref and dest.')
        if any(not isinstance(package[k], str) or not package[k].strip() for k in package):
            raise WorkspaceError(f'{name}: package fields must be nonempty strings.')
        destination(root, package['dest'])
        parts = tuple(p.casefold() for p in PurePosixPath(package['dest']).parts)
        if any(parts[:len(p)] == p or p[:len(parts)] == parts for p in destinations):
            raise WorkspaceError('Overlapping or case-colliding package destinations.')
        destinations.append(parts)
    return packages


def tree_hash(path):
    """Detect edits, additions, deletions and links; never follows linked children."""
    entries = []
    for base, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            item = Path(base) / name
            if is_link(item):
                raise WorkspaceError('Snapshot contains an unexpected link; refusing to replace it.')
            relative = item.relative_to(path).as_posix()
            entries.append(relative + ('/' if item.is_dir() else ':' + hashlib.sha256(item.read_bytes()).hexdigest()))
    return hashlib.sha256('\n'.join(sorted(entries)).encode()).hexdigest()


def read_state(root):
    path = root / '.workspace/state.json'
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise WorkspaceError('Cannot read workspace state; preserve content and inspect .workspace/state.json.') from exc
    if not isinstance(state, dict):
        raise WorkspaceError('Invalid workspace state.')
    return state


def owned_destination(root, dest, state):
    path = destination(root, dest)
    record = state.get(dest)
    if not exists(path):
        return
    if not record:
        raise WorkspaceError(f'{dest}: unmanaged content exists; move it aside first.')
    if record.get('mode') == 'local':
        if not is_link(path) or str(path.resolve()) != record.get('path'):
            raise WorkspaceError(f'{dest}: development link changed outside the workspace tool.')
    elif record.get('mode') == 'snapshot':
        if is_link(path) or not path.is_dir() or tree_hash(path) != record.get('tree_sha256'):
            raise WorkspaceError(f'{dest}: fetched content was modified; preserve your changes before fetching.')
    else:
        raise WorkspaceError(f'{dest}: unknown ownership state.')


def remove_owned(root, dest, state):
    owned_destination(root, dest, state)
    path = destination(root, dest)
    if not exists(path):
        return
    if is_link(path):
        # A Windows junction must be removed as a link, never with recursive deletion.
        if path.is_symlink():
            path.unlink()
        else:
            os.rmdir(path)
    else:
        # This absolute target was validated inside root and fingerprinted above.
        shutil.rmtree(path)


def json_write(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(document, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def repository_location(root, repo):
    if re.match(r'^[A-Za-z][A-Za-z0-9+.-]*://', repo) or re.match(r'^[^/\\:]+@[^/\\:]+:', repo):
        return repo
    return str((root / repo).resolve())


def checkout_archive(root, name, package, ref):
    if ref.startswith('-') or any(c in ref for c in ['\n', '\r', '\0']):
        raise WorkspaceError(f'{name}: invalid Git reference.')
    repo = repository_location(root, package['repo'])
    key = hashlib.sha256(repo.encode()).hexdigest()[:24]
    cache = root / '.workspace/cache' / key
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(['git', 'init', '--bare', str(cache)], capture_output=True)
        if result.returncode:
            raise WorkspaceError('Cannot initialize Git cache.')
    # Fetch an explicit ref even when it is a SHA: an unpublished local commit must not
    # accidentally pass CI simply because it happened to exist in a previous cache.
    git(cache, 'fetch', '--no-tags', '--', repo, ref)
    sha = git(cache, 'rev-parse', '--verify', 'FETCH_HEAD^{commit}')
    data = git(cache, 'archive', '--format=tar', sha, binary=True)
    return sha, data


def extract_snapshot(data, folder):
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        for item in archive.getmembers():
            parts = PurePosixPath(item.name).parts
            if (PurePosixPath(item.name).is_absolute() or PureWindowsPath(item.name).is_absolute() or
                    '..' in parts or not parts or '\\' in item.name or ':' in item.name or
                    '.git' in parts or not (item.isfile() or item.isdir())):
                raise WorkspaceError('Package archive contains an unsafe path, link or special file.')
        archive.extractall(folder, filter='data')


def link_directory(path, target):
    if os.name == 'nt':
        # No destructive operation is composed across shells. mklink only creates a
        # new junction; both paths are absolute, validated, and supplied as arguments.
        if any(ch in str(p) for p in (path, target) for ch in ['"', '\r', '\n', '%', '!', '&', '|', '<', '>','^']):
            raise WorkspaceError('Unsupported shell metacharacter in junction path.')
        result = subprocess.run(['cmd', '/d', '/c', 'mklink', '/J', str(path), str(target)], capture_output=True)
        if result.returncode:
            raise WorkspaceError('Cannot create Windows junction.')
    else:
        path.symlink_to(target, target_is_directory=True)


def local_identity(path):
    # A plain directory is allowed, but is explicitly reported as unversioned.
    if not (path / '.git').exists():
        return {'commit': None, 'dirty': True, 'versioned': False}
    return {'commit': git(path, 'rev-parse', 'HEAD'),
            'branch': git(path, 'rev-parse', '--abbrev-ref', 'HEAD'),
            'dirty': bool(git(path, 'status', '--porcelain', '--untracked-files=all')),
            'versioned': True}


def fetch(root, overrides=None, ref_override=None):
    root = root.resolve()
    packages = manifest(root)
    local = load_yaml(overrides).get('overrides', {}) if overrides else {}
    if not isinstance(local, dict) or set(local) - set(packages):
        raise WorkspaceError('Local overrides contain unknown packages or are not a mapping.')
    if os.getenv('CI') and local:
        raise WorkspaceError('CI rejects local-path overrides.')
    selected = {}
    if ref_override:
        name, separator, ref = ref_override.partition('=')
        if not separator or name not in packages or not ref or name in local:
            raise WorkspaceError('--ref requires a known Package=ref, without a local override for that package.')
        selected[name] = ref
    if os.getenv('CI'):
        for name, package in packages.items():
            if repository_location(root, package['repo']) == str((root / package['repo']).resolve()):
                raise WorkspaceError(f'{name}: CI requires a published remote repository, not a local bootstrap path.')
    state = read_state(root)
    # Preflight the entire workspace before fetching or replacing any destination.
    for dest in set(state) | {p['dest'] for p in packages.values()}:
        owned_destination(root, dest, state)
    resolved = {}
    with tempfile.TemporaryDirectory(prefix='neocam-assemble-') as temporary:
        staging = Path(temporary)
        for name, package in packages.items():
            dest = package['dest']
            if name in local:
                value = local[name]
                if not isinstance(value, dict) or set(value) != {'path'} or not isinstance(value['path'], str):
                    raise WorkspaceError(f'{name}: local override requires a path string.')
                target = (root / value['path']).resolve()
                if not target.is_dir() or target == root or root in target.parents or target in root.parents:
                    raise WorkspaceError(f'{name}: override must be an existing directory outside the integration project.')
                resolved[name] = {'dest': dest, 'mode': 'local', 'path': str(target), **local_identity(target)}
            else:
                ref = selected.get(name, package['ref'])
                sha, archive = checkout_archive(root, name, package, ref)
                folder = staging / name
                folder.mkdir()
                extract_snapshot(archive, folder)
                resolved[name] = {'dest': dest, 'mode': 'snapshot', 'ref': ref,
                                  'commit': sha, 'tree_sha256': tree_hash(folder)}
        # Reject managed cross-package target aliases before making links.
        for item in resolved.values():
            if item['mode'] == 'local' and any(
                    Path(item['path']) == destination(root, p['dest']).resolve() for p in packages.values()):
                raise WorkspaceError('Override aliases a managed package destination.')
        wanted = {p['dest'] for p in packages.values()}
        for old in set(state) - wanted:
            remove_owned(root, old, state)
            del state[old]
            json_write(root / '.workspace/state.json', state)
        for name, record in resolved.items():
            dest = record['dest']
            previous = state.get(dest, {})
            unchanged = (previous.get('mode') == record['mode'] and
                         ((record['mode'] == 'snapshot' and previous.get('tree_sha256') == record['tree_sha256']) or
                          (record['mode'] == 'local' and previous.get('path') == record['path'])))
            # A second check protects edits made while network operations were running.
            owned_destination(root, dest, state)
            path = destination(root, dest)
            if not unchanged or not exists(path):
                remove_owned(root, dest, state)
                path.parent.mkdir(parents=True, exist_ok=True)
                if record['mode'] == 'local':
                    link_directory(path, Path(record['path']))
                else:
                    shutil.copytree(staging / name, path)
            state[dest] = record
            json_write(root / '.workspace/state.json', state)
    json_write(root / '_out/packages-resolved.json', {'packages': resolved})
    return resolved


def status(root):
    packages = manifest(root)
    state = read_state(root)
    report = {}
    for name, package in packages.items():
        dest = package['dest']
        record = dict(state.get(dest, {}))
        try:
            owned_destination(root, dest, state)
            if not exists(destination(root, dest)):
                record['status'] = 'missing'
            elif record.get('mode') == 'local':
                record.update(local_identity(Path(record['path'])))
                record['status'] = 'local-dirty' if record['dirty'] else 'local-clean'
            else:
                record['status'] = 'snapshot'
                record['selection_changed'] = record.get('ref') != package['ref']
        except WorkspaceError as exc:
            record['status'] = str(exc)
        report[name] = record
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['fetch', 'status'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--overrides', type=Path, help='Explicit local-path override YAML; never loaded implicitly')
    parser.add_argument('--ref', help='Override one Package=branch/tag/SHA for this fetch only')
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        if args.command == 'status':
            print(json.dumps(status(root), indent=2))
        else:
            overrides = (root / args.overrides).resolve() if args.overrides else None
            records = fetch(root, overrides, args.ref)
            for name, record in records.items():
                identity = record.get('commit') or 'unversioned'
                print(f'{name}: {record["mode"]} {identity}')
    except (WorkspaceError, OSError, ValueError) as exc:
        print(f'workspace: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
