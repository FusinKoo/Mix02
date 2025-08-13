song ?= MySong
preset ?= best-quality
.PHONY: all runpy prep stems lead dry index rvc tracks bus qc finalize
all: runpy
runpy:; python scripts/run_pipeline.py $(song) $(preset)
prep:;  python -m bin.prep_audio --in input/$(song).wav --outdir work/$(song)/stage-05
stems:; python -m bin.separate_stems --in work/$(song)/stage-05/master_48k32f.wav --outdir work/$(song)/stage-10 --preset $(preset)
lead:;  python -m bin.extract_lead --in work/$(song)/stage-10/Vocal.raw --outdir work/$(song)/stage-21 --preset $(preset)
dry:;  python -m bin.dereverb_denoise --in work/$(song)/stage-21/Lead.raw --outdir work/$(song)/stage-25 --preset $(preset)
index:; python -m bin.build_rvc_index --in assets/guide.wav --out models/rvc/G_8200.index || true
rvc:;   python -m bin.rvc_convert --in work/$(song)/stage-25/Lead_DRY.raw --outdir work/$(song)/stage-35 --preset $(preset)
tracks:
	python -m bin.track_chain --in work/$(song)/stage-10/Drums.raw --outdir work/$(song)/stage-40 --target-lufs -19 --tp -2.5
	python -m bin.track_chain --in work/$(song)/stage-10/Bass.raw  --outdir work/$(song)/stage-41 --target-lufs -19 --tp -2.5
	python -m bin.track_chain --in work/$(song)/stage-10/Other.raw --outdir work/$(song)/stage-42 --target-lufs -19 --tp -2.5
	python -m bin.track_chain --in work/$(song)/stage-35/Lead_RVC.raw --outdir work/$(song)/stage-43 --target-lufs -17 --tp -2
bus:;   python -m bin.mix_bus --lead work/$(song)/stage-43/04_Lead_RVC_processed.wav --drums work/$(song)/stage-40/01_Drums_stem.wav --bass work/$(song)/stage-41/02_Bass_stem.wav --other work/$(song)/stage-42/03_Other_stem.wav --outdir output/$(song) --target-lufs -16 --tp -3
qc:;    python -m bin.qc_report --in output/$(song) --outdir output/$(song)
finalize:; python -m bin.finalize_run --song $(song) --outdir output/$(song)
