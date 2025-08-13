#!/usr/bin/env python3
import argparse, json, sys, os, hashlib, datetime, pathlib
try:
    import yaml
except ImportError:
    yaml = None

def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''):
            h.update(chunk)
    return h.hexdigest()

def write_json(p: str, obj: dict):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def load_preset(name: str):
    here = pathlib.Path(__file__).resolve().parents[1]
    if yaml is None:
        raise FileNotFoundError("PyYAML not installed")
    preset = here / "presets" / f"{name}.yaml"
    return yaml.safe_load(open(preset, "r", encoding="utf-8"))

def sidecar(out_path: str, stage: str, preset: str, overrides: dict):
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    obj = {
        'input': None, 'output': os.path.abspath(out_path), 'stage': stage,
        'sha256': sha256_file(out_path) if os.path.exists(out_path) else None,
        'samplerate': 48000, 'bit_depth': 32, 'channels': 2,
        'metrics': {'peak_dbfs': None, 'integrated_lufs': None, 'true_peak_dbtp': None, 'duration_sec': None},
        'params': {'preset': preset, 'overrides': overrides},
        'timestamp': now, 'status': 'ok'
    }
    return obj

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='inp')
    ap.add_argument('--outdir', default='.')
    ap.add_argument('--out', dest='out')
    ap.add_argument('--preset', default='best-quality')
    ap.add_argument('--override', action='append', default=[])
    ap.add_argument('--log-json')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    try:
        ov = {}
        for item in args.override:
            if '=' in item:
                k, v = item.split('=', 1)
                ov[k] = v
        _ = load_preset(args.preset)
        os.makedirs(args.outdir, exist_ok=True)
        stems = ['Vocal.raw', 'Drums.raw', 'Bass.raw', 'Other.raw']
        for stem in stems:
            path = os.path.join(args.outdir, stem)
            if not os.path.exists(path) or args.force:
                open(path, 'wb').close()
            sc = sidecar(path, stage=os.path.basename(__file__).replace('.py',''), preset=args.preset, overrides=ov)
            sc['input'] = os.path.abspath(args.inp) if args.inp else None
            write_json(path + '.json', sc)
        if args.log_json:
            with open(args.log_json, 'a', encoding='utf-8') as lj:
                ts = datetime.datetime.utcnow().isoformat() + 'Z'
                lj.write(json.dumps({'stage': os.path.basename(__file__).replace('.py',''), 'output': os.path.abspath(os.path.join(args.outdir, stems[0])), 'ts': ts}) + '\n')
        return 0
    except FileNotFoundError as e:
        err = {'stage': os.path.basename(__file__), 'error_code': 22, 'error_type': 'ModelOrPresetMissing', 'message': str(e)}
        write_json(os.path.join(args.outdir, 'error.json'), err)
        return 22
    except Exception as e:
        err = {'stage': os.path.basename(__file__), 'error_code': 1, 'error_type': e.__class__.__name__, 'message': str(e)}
        write_json(os.path.join(args.outdir, 'error.json'), err)
        return 1

if __name__ == '__main__':
    sys.exit(main())
