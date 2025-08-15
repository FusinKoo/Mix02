from __future__ import annotations
import argparse, json, os, datetime, hashlib, pathlib, subprocess, shutil
try:  # optional dependency
    import yaml  # type: ignore
except Exception:  # pragma: no cover - fallback when PyYAML absent
    yaml = None

ROOT = pathlib.Path(__file__).resolve().parents[1]

def ensure_dir(p: str | os.PathLike) -> str:
    """Create directory *p* if missing and return the path as string."""
    os.makedirs(p, exist_ok=True)
    return str(p)

def run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess command and return the completed process."""
    return subprocess.run(cmd, check=True, text=True, capture_output=True)

def sha256sum(p: str) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

# backward compat
sha256_file = sha256sum

def write_json(path: str | os.PathLike, data: dict):
    ensure_dir(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def dry_run_guard(args, plan: dict) -> bool:
    """Print plan and return True if in dry-run mode."""
    if getattr(args, 'dry_run', False):
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return True
    return False

def ffprobe_json(p: str) -> dict:
    try:
        proc = run_cmd(['ffprobe', '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', p])
        return json.loads(proc.stdout)
    except Exception:
        return {}

def load_preset(name: str) -> dict:
    p = ROOT / 'presets' / f'{name}.yaml'
    if yaml is None:
        return {}
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

def sidecar(out_path: str, stage: str, preset: str, overrides: dict, inp: str | None):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    sc = {
        'input': os.path.abspath(inp) if inp else None,
        'output': os.path.abspath(out_path),
        'stage': stage,
        'sha256': sha256sum(out_path) if os.path.exists(out_path) else None,
        'samplerate': 48000,
        'bit_depth': 32,
        'channels': 2,
        'metrics': {
            'peak_dbfs': None,
            'integrated_lufs': None,
            'true_peak_dbtp': None,
            'duration_sec': None
        },
        'params': {'preset': preset, 'overrides': overrides},
        'timestamp': now,
        'status': 'ok'
    }
    return sc

def emit_log(log_path: str | None, payload: dict):
    if not log_path:
        return
    ensure_dir(os.path.dirname(log_path))
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(payload, ensure_ascii=False) + '\n')

