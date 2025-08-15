from __future__ import annotations
import argparse, json, os, sys, platform, shutil
from . import _utils as u

STAGE = '00-env_probe'

def probe_env() -> dict:
    info = {
        'python': platform.python_version(),
        'ffmpeg_version': None,
        'cuda_available': False,
        'torch_version': None,
        'gpu': None,
        'cpu_count': os.cpu_count(),
        'disk_free_gb': shutil.disk_usage('.').free / 1e9,
    }
    try:
        proc = u.run_cmd(['ffmpeg', '-version'])
        info['ffmpeg_version'] = proc.stdout.splitlines()[0]
    except Exception:
        info['ffmpeg_version'] = None
    try:
        import torch
        info['torch_version'] = torch.__version__
        info['cuda_available'] = bool(torch.cuda.is_available())
        if info['cuda_available']:
            info['gpu'] = torch.cuda.get_device_name(0)
    except Exception:
        pass
    return info

def main():
    ap = argparse.ArgumentParser()
    u.add_common_args(ap)
    args = ap.parse_args()
    u.load_preset(args.preset)
    ov = u.parse_overrides(args.override)
    out_path = args.out or os.path.join(args.outdir, 'env.json')
    u.ensure_dir(os.path.dirname(out_path))
    plan = {'stage': STAGE, 'plan_output': os.path.abspath(out_path)}
    if u.dry_run_guard(args, plan):
        return 0
    data = probe_env()
    u.write_json(out_path, data)
    sc = u.sidecar(out_path, STAGE, args.preset, ov, args.inp)
    u.write_json(out_path + '.json', sc)
    u.emit_log(args.log_json, {'stage': STAGE, 'output': out_path})
    return 0

if __name__ == '__main__':
    sys.exit(main())
