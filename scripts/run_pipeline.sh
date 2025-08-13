#!/usr/bin/env bash
set -euo pipefail
SONG="$1"
PRESET="${2:-best-quality}"
ROOT=$(cd "$(dirname "$0")/.." && pwd)
W="$ROOT/work/$SONG"
O="$ROOT/output/$SONG"
mkdir -p "$W" "$O"
python -m bin.env_probe       --outdir "$W/stage-00"
python -m bin.prep_audio      --in "$ROOT/input/$SONG.wav" --outdir "$W/stage-05"
python -m bin.separate_stems  --in "$W/stage-05/master_48k32f.wav" --outdir "$W/stage-10" --preset "$PRESET"
python -m bin.extract_lead    --in "$W/stage-10/Vocal.raw" --outdir "$W/stage-21" --preset "$PRESET"
python -m bin.dereverb_denoise --in "$W/stage-21/Lead.raw" --outdir "$W/stage-25" --preset "$PRESET"
python -m bin.build_rvc_index --in "$ROOT/assets/guide.wav" --out "$ROOT/models/rvc/G_8200.index" || true
python -m bin.rvc_convert     --in "$W/stage-25/Lead_DRY.raw" --outdir "$W/stage-35" --preset "$PRESET"
python -m bin.track_chain     --in "$W/stage-10/Drums.raw" --outdir "$W/stage-40" --target-lufs -19 --tp -2.5
python -m bin.track_chain     --in "$W/stage-10/Bass.raw"  --outdir "$W/stage-41" --target-lufs -19 --tp -2.5
python -m bin.track_chain     --in "$W/stage-10/Other.raw" --outdir "$W/stage-42" --target-lufs -19 --tp -2.5
python -m bin.track_chain     --in "$W/stage-35/Lead_RVC.raw" --outdir "$W/stage-43" --target-lufs -17 --tp -2
python -m bin.mix_bus         --lead "$W/stage-43/04_Lead_RVC_processed.wav" \
  --drums "$W/stage-40/01_Drums_stem.wav" --bass "$W/stage-41/02_Bass_stem.wav" \
  --other "$W/stage-42/03_Other_stem.wav" --outdir "$O" --target-lufs -16 --tp -3
python -m bin.qc_report       --in "$O" --outdir "$O"
python -m bin.finalize_run    --song "$SONG" --outdir "$O"
