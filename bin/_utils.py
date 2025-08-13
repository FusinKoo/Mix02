from __future__ import annotations
import argparse, json, os, datetime, hashlib, pathlib, yaml

def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def load_preset(name: str) -> dict:
    root = pathlib.Path(__file__).resolve().parents[1]
    p = root / 'presets' / f'{name}.yaml'
    with open(p, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def add_common_args(ap: argparse.ArgumentParser):
    ap.add_argument('--in', dest='inp')
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--out')
    ap.add_argument('--preset', default='best-quality')
    ap.add_argument('--override', action='append', default=[])
    ap.add_argument('--log-json')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--dry-run', action='store_true')

def parse_overrides(items: list[str]) -> dict:
    ov = {}
    for it in items or []:
        if '=' in it:
            k, v = it.split('=', 1)
            ov[k] = v
    return ov

def sidecar(out_path: str, stage: str, preset: str, overrides: dict, inp: str|None):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    sc = {
        'input': os.path.abspath(inp) if inp else None,
        'output': os.path.abspath(out_path),
        'stage': stage,
        'sha256': sha256_file(out_path) if os.path.exists(out_path) else None,
        'samplerate': 48000,
        'bit_depth': 32,
        'channels': 2,
        'metrics': {'peak_dbfs': None, 'integrated_lufs': None, 'true_peak_dbtp': None, 'duration_sec': None},
        'params': {'preset': preset, 'overrides': overrides},
        'timestamp': now,
        'status': 'ok'
    }
    return sc

def emit_log(log_path: str|None, payload: dict):
    if not log_path: return
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')
