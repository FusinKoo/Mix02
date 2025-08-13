from __future__ import annotations
import argparse, json, os, sys
from . import _utils as u

STAGE = '25-dereverb_denoise'

def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    args = ap.parse_args()
    u.load_preset(args.preset)
    ov = u.parse_overrides(args.override)
    out_path = args.out or os.path.join(args.outdir, 'Lead_DRY.raw')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plan = {'stage': STAGE, 'plan_output': os.path.abspath(out_path)}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    open(out_path, 'w', encoding='utf-8').write('dry\n')
    sc = u.sidecar(out_path, STAGE, args.preset, ov, args.inp)
    with open(out_path + '.json', 'w', encoding='utf-8') as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
    u.emit_log(args.log_json, {'stage': STAGE, 'output': out_path})
    return 0

if __name__ == '__main__':
    sys.exit(main())
