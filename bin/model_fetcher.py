from __future__ import annotations
import argparse, json, os, sys, pathlib, urllib.request, shutil, hashlib
from . import _utils as u

STAGE = '00-model_fetcher'
ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_DEFAULT = ROOT / 'models' / 'registry.json'


def download(url: str, dest: pathlib.Path):
    with urllib.request.urlopen(url) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)


def fetch(entry: dict, force: bool) -> tuple[pathlib.Path, str | None]:
    filename = os.path.basename(entry['urls'][0])
    dest = ROOT / 'models' / filename
    if dest.exists() and not force:
        return dest, None
    last_err: Exception | None = None
    for url in entry['urls']:
        try:
            u.ensure_dir(dest.parent)
            download(url, dest)
            if entry.get('size') and dest.stat().st_size != entry['size']:
                raise RuntimeError('size mismatch')
            if entry.get('sha256'):
                h = u.sha256sum(dest)
                if h != entry['sha256']:
                    raise RuntimeError('sha256 mismatch')
            return dest, None
        except Exception as e:  # pragma: no cover - network failures
            last_err = e
            if dest.exists():
                dest.unlink()
    return dest, str(last_err) if last_err else 'unknown error'


def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    ap.add_argument('--registry', default=str(REGISTRY_DEFAULT))
    ap.add_argument('--name', nargs='*')
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    with open(args.registry, 'r', encoding='utf-8') as f:
        reg_list = json.load(f)
    registry = {it['name']: it for it in reg_list}
    targets = list(registry.keys()) if args.all or not args.name else args.name
    plan = [str(ROOT / 'models' / os.path.basename(registry[n]['urls'][0])) for n in targets]
    if u.dry_run_guard(args, {'stage': STAGE, 'plan_outputs': plan}):
        return 0
    missing = []
    for n in targets:
        dest, err = fetch(registry[n], args.force)
        if err:
            missing.append({'name': n, 'error': err})
    if missing:
        u.write_json(ROOT / 'missing_models.json', {'missing': missing})
        u.emit_log(args.log_json, {'stage': STAGE, 'missing': missing})
        return 22
    u.emit_log(args.log_json, {'stage': STAGE, 'status': 'ok'})
    return 0


if __name__ == '__main__':
    sys.exit(main())

