from __future__ import annotations
import argparse, json, os, sys
from . import _utils as u

STAGE = '50-mix_bus'

def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    ap.add_argument('--lead')
    ap.add_argument('--drums')
    ap.add_argument('--bass')
    ap.add_argument('--other')
    ap.add_argument('--target-lufs', type=float, default=-16)
    ap.add_argument('--tp', type=float, default=-3.0)
    args = ap.parse_args()
    u.load_preset(args.preset)
    ov = u.parse_overrides(args.override)
    song = os.path.basename(os.path.abspath(args.outdir))
    out_path = args.out or os.path.join(args.outdir, f'99_Final_{song}_mix_24b48k.wav')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plan = {'stage': STAGE, 'plan_output': os.path.abspath(out_path)}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    open(out_path, 'w', encoding='utf-8').write('mix\n')
    sc = u.sidecar(out_path, STAGE, args.preset, ov, args.inp)
    with open(out_path + '.json', 'w', encoding='utf-8') as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
    u.emit_log(args.log_json, {'stage': STAGE, 'output': out_path})
    return 0

if __name__ == '__main__':
    sys.exit(main())
