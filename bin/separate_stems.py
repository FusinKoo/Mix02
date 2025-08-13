from __future__ import annotations
import argparse, json, os, sys
from . import _utils as u

STAGE = '10-separate_stems'
STEMS = ['Vocal.raw', 'Drums.raw', 'Bass.raw', 'Other.raw']

def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    args = ap.parse_args()
    u.load_preset(args.preset)
    ov = u.parse_overrides(args.override)
    outputs = [os.path.join(args.outdir, s) for s in STEMS]
    for p in outputs:
        os.makedirs(os.path.dirname(p), exist_ok=True)
    plan = {'stage': STAGE, 'plan_outputs': [os.path.abspath(p) for p in outputs]}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    for out_path in outputs:
        open(out_path, 'w', encoding='utf-8').write('stem\n')
        sc = u.sidecar(out_path, STAGE, args.preset, ov, args.inp)
        with open(out_path + '.json', 'w', encoding='utf-8') as f:
            json.dump(sc, f, ensure_ascii=False, indent=2)
    u.emit_log(args.log_json, {'stage': STAGE, 'outputs': outputs[0]})
    return 0

if __name__ == '__main__':
    sys.exit(main())
