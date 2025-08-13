from __future__ import annotations
import argparse, json, os, sys, shutil, pathlib
from typing import List, Dict, Any
from . import _utils as u

STAGE = '00-model_fetcher'

ROOT = pathlib.Path(__file__).resolve().parents[1]
REGISTRY_DEFAULT = ROOT / 'models' / 'registry.json'


def parse_hf_source(src: str):
    spec = src[3:]
    if ':' in spec:
        repo, rest = spec.split(':', 1)
    else:
        repo, rest = spec, ''
    revision = None
    filename = rest
    if rest.startswith('resolve/'):
        _, revision, filename = rest.split('/', 2)
    return repo, filename, revision


def download_hf(src: str, dest: pathlib.Path):
    from huggingface_hub import hf_hub_download
    repo, filename, revision = parse_hf_source(src)
    tmp = hf_hub_download(repo_id=repo, filename=filename, revision=revision)
    os.makedirs(dest.parent, exist_ok=True)
    shutil.copyfile(tmp, dest)


def fetch_files(items: List[Dict[str, Any]], force: bool, missing: List[Dict[str, str]]):
    for it in items:
        dest = ROOT / it['path']
        if dest.exists() and not force:
            continue
        try:
            src = it['source']
            if src.startswith('hf:'):
                download_hf(src, dest)
            else:
                raise RuntimeError(f'Unsupported source {src}')
            if it.get('sha256'):
                if u.sha256_file(str(dest)) != it['sha256']:
                    raise RuntimeError('sha256 mismatch')
        except Exception as e:
            missing.append({'file': it['path'], 'error': str(e)})


def fetch_demucs(models: List[str], missing: List[Dict[str, str]]):
    try:
        import demucs.pretrained
        for m in models:
            try:
                demucs.pretrained.get_model(m)
            except Exception as e:
                missing.append({'demucs_model': m, 'error': str(e)})
    except Exception as e:
        missing.append({'provider': 'demucs', 'error': str(e)})


def build_plan(registry: Dict[str, Any]) -> List[str]:
    plan = []
    for sec in registry.values():
        if sec.get('files'):
            for it in sec['files']:
                plan.append(str(ROOT / it['path']))
        if sec.get('provider') == 'pip-demucs':
            for m in sec.get('models', []):
                plan.append(f'demucs:{m}')
    return plan


def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    ap.add_argument('--registry', default=str(REGISTRY_DEFAULT))
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    reg_path = pathlib.Path(args.registry)
    with open(reg_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    plan = build_plan(registry)
    if args.dry_run:
        print(json.dumps({'stage': STAGE, 'plan_outputs': plan}, ensure_ascii=False, indent=2))
        return 0
    missing: List[Dict[str, str]] = []
    for name, sec in registry.items():
        if sec.get('provider') == 'pip-demucs':
            fetch_demucs(sec.get('models', []), missing)
        if sec.get('files'):
            fetch_files(sec['files'], args.force, missing)
    if missing:
        miss_path = ROOT / 'missing_models.json'
        with open(miss_path, 'w', encoding='utf-8') as f:
            json.dump({'missing': missing}, f, ensure_ascii=False, indent=2)
        u.emit_log(args.log_json, {'stage': STAGE, 'missing': missing})
        return 22
    u.emit_log(args.log_json, {'stage': STAGE, 'status': 'ok'})
    return 0


if __name__ == '__main__':
    sys.exit(main())
