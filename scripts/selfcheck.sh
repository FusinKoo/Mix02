#!/usr/bin/env bash
set -e
CLIS=(env_probe prep_audio separate_stems extract_lead dereverb_denoise build_rvc_index rvc_convert track_chain mix_bus qc_report finalize_run)
for c in "${CLIS[@]}"; do
  python -m bin.$c --help >/dev/null
  if [ "$c" = "finalize_run" ]; then
    python -m bin.$c --song Test --dry-run >/dev/null
  else
    python -m bin.$c --dry-run >/dev/null
  fi
done
