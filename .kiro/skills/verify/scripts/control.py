#!/usr/bin/env python3
"""Run real offline iDSN CLIs in a credential-free source copy."""
from __future__ import annotations
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
SOURCES = ('harness/run_experiment.py', 'harness/analyze.py', 'client/vmssh.py',
           'tools/validate_pacer.py', 'configs/params_schema.json')


def save(path, value):
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(work):
    return {p.relative_to(work).as_posix(): digest(p)
            for p in sorted(work.rglob('*')) if p.is_file()}


def refs():
    r = subprocess.run(['git', 'show-ref', '--head'], cwd=ROOT, capture_output=True, check=True)
    return hashlib.sha256(r.stdout).hexdigest()


def versions():
    return {n: importlib.metadata.version(n) for n in ('requests', 'websocket-client')}


def guarded_exec():
    work, script, *args = sys.argv[2:]
    work = Path(work).resolve()
    os.chdir(work)
    with (work.parent / 'boundary-events.jsonl').open('a', encoding='utf-8') as events:
        def audit(event, values):
            blocked = event in {'socket.connect', 'socket.bind', 'socket.getaddrinfo',
                               'socket.sendto', 'socket.sendmsg', 'subprocess.Popen',
                               'os.system', 'os.exec', 'os.posix_spawn'}
            paths = []
            if event == 'open' and not isinstance(values[0], int):
                path, mode, flags = values
                if Path(path).name.startswith('secrets') or str(path).endswith(('.pkl', '.pickle')):
                    blocked = True
                if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
                    paths.append(path)
            elif event in {'os.remove', 'os.rmdir', 'os.mkdir', 'shutil.rmtree'}:
                paths.append(values[0])
            elif event in {'os.rename', 'os.link', 'os.symlink'}:
                paths.extend(values[:2])
            if any(not Path(p).resolve().is_relative_to(work) for p in paths):
                blocked = True
            if blocked:
                events.write(json.dumps({'blocked': event}) + '\n')
                events.flush()
                raise PermissionError(f'verification boundary blocked: {event}')
        sys.addaudithook(audit)
        sys.argv = [script, *args]
        sys.path.insert(0, str((work / script).parent))
        runpy.run_path(str(work / script), run_name='__main__')


def command(work, label, script, *args, expected=0):
    env = {k: v for k, v in os.environ.items() if not k.startswith('IDSN_')}
    env.update(PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1', IDSN_VM_PASS='verification-unused',
               TMP=str(work / 'tmp'), TEMP=str(work / 'tmp'), TMPDIR=str(work / 'tmp'))
    argv = [sys.executable, '-B', '-X', 'utf8', str(Path(__file__).resolve()),
            '_exec', str(work), script, *args]
    before = snapshot(work)
    r = subprocess.run(argv, cwd=work, env=env, capture_output=True,
                       text=True, encoding='utf-8', timeout=30)
    after = snapshot(work)
    save(work.parent / f'{label}.json', {'command': [sys.executable, script, *args],
         'cwd': str(work), 'stdout': r.stdout, 'stderr': r.stderr, 'exit': r.returncode,
         'before': before, 'after': after})
    if r.returncode != expected:
        raise RuntimeError(f'{label}: exit {r.returncode}, expected {expected}; see {label}.json')
    if (work.parent / 'boundary-events.jsonl').stat().st_size:
        raise RuntimeError('Forbidden boundary attempted; inspect boundary-events.jsonl')
    print(f'PASS {label} (exit {r.returncode})')
    return r.stdout, before, after


def doctor(evidence):
    manifest = json.loads((evidence / 'manifest.json').read_text('utf-8'))
    work = evidence / 'work'
    if work.is_symlink() or not work.is_dir():
        raise RuntimeError('No owned workspace; launch a new run')
    if manifest['root'] != str(ROOT) or manifest['python'] != sys.executable:
        raise RuntimeError('Wrong checkout or interpreter')
    for name, sha in manifest['sources'].items():
        if digest(ROOT / name) != sha or digest(work / name) != sha:
            raise RuntimeError(f'Source changed: {name}; launch a fresh run')
    versions()
    print(f'READY {evidence.name}; Python {sys.version.split()[0]}; offline CLI; no service/port')
    return manifest, work


def generate(work):
    _, before, after = command(work, 'generate-uniform', 'harness/run_experiment.py',
        '--tag', 'uniform', '--mode', 'leak_bucket', '--params',
        'leak_rate=9,bucket_cap=30,leak_interval_us=1000', '--dry-run')
    changed = {p for p in set(before) | set(after) if before.get(p) != after.get(p)}
    assert changed == {f'runs/configs/uniform/{i}/pacer.txt' for i in range(1, 7)}, changed
    for i in range(1, 7):
        expected = (f'[timestamp:{i}]\npacer_mode:leak_bucket\npacer_config:'
                    'leak_rate=9,bucket_cap=30,leak_interval_us=1000').encode()
        assert (work / f'runs/configs/uniform/{i}/pacer.txt').read_bytes() == expected
    command(work, 'validate-uniform', 'tools/validate_pacer.py', 'runs/configs/uniform')
    command(work, 'generate-default', 'harness/run_experiment.py', '--tag', 'default', '--dry-run')
    assert sorted(p.name for p in (work / 'runs/configs/default').iterdir()) == list('123456')
    assert not list((work / 'runs/configs/default').rglob('pacer.txt'))
    command(work, 'validate-default', 'tools/validate_pacer.py', 'runs/configs/default', '--json')
    save(work / 'mixed.json', {'1': ['token_bucket', {'tokens': 100, 'burst': 200}], '3': ['origin', {}]})
    command(work, 'generate-mixed', 'harness/run_experiment.py', '--tag', 'mixed',
            '--configs-file', 'mixed.json', '--dry-run')
    assert {p.parent.name for p in (work / 'runs/configs/mixed').rglob('pacer.txt')} == {'1', '3'}
    command(work, 'validate-mixed', 'tools/validate_pacer.py', 'runs/configs/mixed', '--json')
    for tag in ('uniform', 'default', 'mixed'):
        shutil.copytree(work / 'runs/configs' / tag, work.parent / f'config-{tag}')


def validate(work):
    command(work, 'validator-selftest', 'tools/validate_pacer.py', '--selftest')
    for i in range(1, 7):
        (work / f'invalid/{i}').mkdir(parents=True)
    (work / 'invalid/1/pacer.txt').write_bytes(b'[timestamp:1]\r\npacer_mode:origin\r\npacer_config:')
    out, _, _ = command(work, 'validator-reject-crlf', 'tools/validate_pacer.py',
                        'invalid', '--json', expected=1)
    assert not json.loads(out)['ok']
    assert any(e['check'] == 3 for e in json.loads(out)['errors'])


def analyze(work):
    out, _, _ = command(work, 'analysis-empty', 'harness/analyze.py', '--json')
    assert out.strip() == '暂无结果'
    rows = [{'tag': t, 'config': {}, 'total_seconds': s, 'downloads': {}, 'valid': v}
            for t, s, v in (('base', 60, True), ('base', 64, True), ('bad', 1, False))]
    path = work / 'runs/results.jsonl'
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(''.join(json.dumps(row) + '\n' for row in rows).encode())
    shutil.copy2(path, work.parent / 'analysis-input.jsonl')
    out, before, after = command(work, 'analysis-json', 'harness/analyze.py', '--json')
    row = json.loads(out)[0]
    assert row['n'] == 2 and row['mean'] == 62 and before == after
    out, _, _ = command(work, 'analysis-include-invalid', 'harness/analyze.py', '--json', '--include-invalid')
    assert json.loads(out)[0]['n'] == 3
    command(work, 'analysis-table', 'harness/analyze.py', '--tag', 'base')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['launch', 'doctor', 'drive', 'cleanup', 'evidence'])
    ap.add_argument('--run', required=True, help='Fresh lowercase run name; never reuse')
    ap.add_argument('--feature', choices=['generation', 'validation', 'analysis', 'all'], default='all')
    args = ap.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,60}', args.run):
        ap.error('--run must match [a-z0-9][a-z0-9-]{0,60}')
    base = (ROOT / 'runs/evals').resolve()
    evidence = base / f'verify-{args.run}'
    if evidence.is_symlink() or evidence.resolve().parent != base:
        raise RuntimeError('Evidence must be a direct owned child of runs/evals')
    work = evidence / 'work'
    if args.action == 'launch':
        deps = versions()
        evidence.mkdir(parents=True, exist_ok=False)
        manifest = {'root': str(ROOT), 'python': sys.executable, 'version': sys.version,
                    'dependencies': deps, 'sources': {}, 'refs_before': refs()}
        save(evidence / 'manifest.json', manifest)
        (work / 'tmp').mkdir(parents=True)
        for name in SOURCES:
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)
            manifest['sources'][name] = digest(target)
        save(evidence / 'manifest.json', manifest)
        doctor(evidence)
    elif args.action == 'doctor':
        doctor(evidence)
    elif args.action == 'drive':
        manifest, work = doctor(evidence)
        try:
            for name, check in {'generation': generate, 'validation': validate, 'analysis': analyze}.items():
                if args.feature in (name, 'all'):
                    check(work)
            assert refs() == manifest['refs_before'], 'Git refs changed during verification'
            save(evidence / 'proof.json', {'ok': True, 'feature': args.feature,
                 'scope': 'offline CLIs in unchanged source copy; synthetic analysis input',
                 'network_attempts': 0, 'git_refs_unchanged': True})
        except BaseException:
            save(evidence / 'proof.json', {'ok': False, 'feature': args.feature})
            raise
    elif args.action == 'cleanup':
        manifest = json.loads((evidence / 'manifest.json').read_text('utf-8'))
        if manifest['root'] != str(ROOT) or work.is_symlink() or work.resolve().parent != evidence.resolve():
            raise RuntimeError('Refusing cleanup of unowned path')
        if work.exists():
            if any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction()) for p in work.rglob('*')):
                raise RuntimeError('Refusing recursive cleanup through a link/junction')
            shutil.rmtree(work)
        save(evidence / 'cleanup.json', {'work_removed': not work.exists(), 'evidence_retained': True})
        print(f'CLEAN {evidence}')
    else:
        assert not work.exists(), 'Run cleanup first'
        proof = json.loads((evidence / 'proof.json').read_text('utf-8'))
        assert proof['ok'], 'Drive did not pass'
        assert (evidence / 'cleanup.json').is_file()
        assert list(evidence.glob('*-*.json')), 'Command evidence missing'
        if proof['feature'] in ('generation', 'all'):
            assert len(list((evidence / 'config-uniform').glob('*/pacer.txt'))) == 6
        print(f'EVIDENCE PASS {evidence}')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '_exec':
        guarded_exec()
    else:
        main()
