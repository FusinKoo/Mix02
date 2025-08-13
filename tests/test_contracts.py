import subprocess, sys, pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

def run(cmd):
    return subprocess.run(cmd, cwd=ROOT)

class ContractsTest(unittest.TestCase):
    def test_help(self):
        r = run([sys.executable,'-m','bin.env_probe','--help'])
        self.assertEqual(r.returncode, 0)

    def test_dry_run(self):
        outdir = ROOT/'work'/'Dry'/'stage-00'
        outdir.mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable,'-m','bin.env_probe','--outdir',str(outdir),'--dry-run'], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(r.returncode, 0)
        self.assertIn('plan_output', r.stdout)

if __name__ == '__main__':
    unittest.main()
