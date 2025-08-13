#!/usr/bin/env python3
import subprocess, sys, pathlib, os

STAGES = [
  ['python','-m','bin.env_probe'],
  ['python','-m','bin.prep_audio'],
  ['python','-m','bin.separate_stems'],
  ['python','-m','bin.extract_lead'],
  ['python','-m','bin.dereverb_denoise'],
  ['python','-m','bin.build_rvc_index'],
  ['python','-m','bin.rvc_convert'],
  ['python','-m','bin.track_chain'],
  ['python','-m','bin.track_chain'],
  ['python','-m','bin.track_chain'],
  ['python','-m','bin.track_chain'],
  ['python','-m','bin.mix_bus'],
  ['python','-m','bin.qc_report'],
  ['python','-m','bin.finalize_run'],
]

def run(song: str, preset: str='best-quality'):
    root = pathlib.Path(__file__).resolve().parents[1]
    w = root / 'work' / song
    o = root / 'output' / song
    w.mkdir(parents=True, exist_ok=True)
    o.mkdir(parents=True, exist_ok=True)
    cmds = [
      ['python','-m','bin.env_probe','--outdir',str(w/'stage-00')],
      ['python','-m','bin.prep_audio','--in',str(root/'input'/f'{song}.wav'),'--outdir',str(w/'stage-05')],
      ['python','-m','bin.separate_stems','--in',str(w/'stage-05'/'master_48k32f.wav'),'--outdir',str(w/'stage-10'),'--preset',preset],
      ['python','-m','bin.extract_lead','--in',str(w/'stage-10'/'Vocal.raw'),'--outdir',str(w/'stage-21'),'--preset',preset],
      ['python','-m','bin.dereverb_denoise','--in',str(w/'stage-21'/'Lead.raw'),'--outdir',str(w/'stage-25'),'--preset',preset],
      ['python','-m','bin.build_rvc_index','--in',str(root/'assets'/'guide.wav'),'--out',str(root/'models'/'rvc'/'G_8200.index')],
      ['python','-m','bin.rvc_convert','--in',str(w/'stage-25'/'Lead_DRY.raw'),'--outdir',str(w/'stage-35'),'--preset',preset],
      ['python','-m','bin.track_chain','--in',str(w/'stage-10'/'Drums.raw'),'--outdir',str(w/'stage-40'),'--target-lufs','-19','--tp','-2.5'],
      ['python','-m','bin.track_chain','--in',str(w/'stage-10'/'Bass.raw'),'--outdir',str(w/'stage-41'),'--target-lufs','-19','--tp','-2.5'],
      ['python','-m','bin.track_chain','--in',str(w/'stage-10'/'Other.raw'),'--outdir',str(w/'stage-42'),'--target-lufs','-19','--tp','-2.5'],
      ['python','-m','bin.track_chain','--in',str(w/'stage-35'/'Lead_RVC.raw'),'--outdir',str(w/'stage-43'),'--target-lufs','-17','--tp','-2'],
      ['python','-m','bin.mix_bus','--lead',str(w/'stage-43'/'04_Lead_RVC_processed.wav'),'--drums',str(w/'stage-40'/'01_Drums_stem.wav'),'--bass',str(w/'stage-41'/'02_Bass_stem.wav'),'--other',str(w/'stage-42'/'03_Other_stem.wav'),'--outdir',str(o),'--target-lufs','-16','--tp','-3'],
      ['python','-m','bin.qc_report','--in',str(o),'--outdir',str(o)],
      ['python','-m','bin.finalize_run','--song',song,'--outdir',str(o)],
    ]
    for c in cmds:
      print('>>', ' '.join(map(str,c)))
      r = subprocess.run(c)
      if r.returncode != 0:
        sys.exit(r.returncode)

if __name__ == '__main__':
    song = sys.argv[1] if len(sys.argv)>1 else 'MySong'
    preset = sys.argv[2] if len(sys.argv)>2 else 'best-quality'
    run(song, preset)
