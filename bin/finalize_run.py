from __future__ import annotations
import argparse, json, os, sys
from . import _utils as u

STAGE = '99-finalize_run'

def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    ap.add_argument('--song', required=True)
    args = ap.parse_args()
    u.load_preset(args.preset)
    ov = u.parse_overrides(args.override)
    out_path = args.out or os.path.join(args.outdir, 'RUNLOG.json')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plan = {'stage': STAGE, 'plan_output': os.path.abspath(out_path)}
    if args.dry_run:
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0
    for legacy in [os.path.join(args.outdir, 'final_mix.wav'), os.path.join(args.outdir, f'{args.song}_done.txt')]:
        if os.path.exists(legacy):
            print(f'removing legacy artifact: {legacy}')
            os.remove(legacy)
            if os.path.exists(legacy + '.json'):
                os.remove(legacy + '.json')
    payload = {'stages': [], 'ok': True}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    sc = u.sidecar(out_path, STAGE, args.preset, ov, args.inp)
    with open(out_path + '.json', 'w', encoding='utf-8') as f:
        json.dump(sc, f, ensure_ascii=False, indent=2)
    u.emit_log(args.log_json, {'stage': STAGE, 'output': out_path})
    return 0

if __name__ == '__main__':
    sys.exit(main())
