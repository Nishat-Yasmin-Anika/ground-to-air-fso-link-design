"""Build the portable notebook from canonical repository files (no duplicated editing)."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
DEST=ROOT/'notebooks/FSO_Link_Design_Colab.ipynb'
FILES=['src/atmosphere.py','src/fso_link.py','run_study.py','tests/test_link.py','tests/test_audit.py',
       'README.md','docs/SOURCE_MAP.md','docs/TECHNICAL_NOTE.md','docs/COMPLEXITY_AND_VERIFICATION.md',
       'results/README.md','requirements.txt','requirements-lock.txt','verify_manifest.py','build_notebook.py',
       'UPDATE_GITHUB.md','.github/workflows/python-tests.yml']

def build():
    cells=[]
    def add(kind,source):
        c={'cell_type':kind,'id':hashlib.sha256(f'{len(cells)}:{kind}'.encode()).hexdigest()[:12],
           'metadata':{},'source':source.splitlines(keepends=True)}
        if kind=='code':c.update(execution_count=None,outputs=[])
        cells.append(c)
    add('markdown', '''# Atmospheric-model sensitivity in ground-to-air FSO receiver design — v4
**Nishat Yasmin Anika · ECE · KUET**  
Standalone CPU notebook generated from canonical source files. Run all cells in order; no Drive mount required.

**Scope:** conditional optical-power availability, not BER, measured uptime or practical receiver specifications. Literal dB/km is the primary convention; equation-as-printed is a legacy comparison only. Table II, the clear-weather prose alternative and the hypothetical radiation-fog stress case are kept separate. No source MODTRAN data or field observations were reproduced. See the embedded source map.

The original repository is [ground-to-air-fso-link-design](https://github.com/Nishat-Yasmin-Anika/ground-to-air-fso-link-design). AI tools assisted code revision and review; author approval is required before publication.''')
    add('markdown','''## 1. Mathematical model and verification
For integrated power attenuation $Q$ in dB, $T=10^{-Q/10}$. If the printed quantity instead represents Napierian optical depth, $T=e^{-Q}$. A circular aperture captures $G=F_{\\chi'^2_2}((2a/w)^2;\\lambda=(2r/w)^2)$ from a displaced Gaussian spot. Independent equal-variance transverse Gaussian jitter implies Rayleigh radial displacement. Received power is $P=P_{tx}\\eta T G$; availability is $\\Pr(P\\ge P_{min})$. TV robustness minimizes the scenario-weighted success probability over a half-L1 probability ball. Feasible-endpoint bisection finds the minimum radius in the specified search interval, including threshold steps at zero jitter. All inputs are conditional assumptions. See the embedded technical note for derivations and limitations.''')
    add('code','''import sys, subprocess, importlib.util
from pathlib import Path
missing = [p for p in ('numpy','scipy','matplotlib') if importlib.util.find_spec(p) is None]
if missing:
    subprocess.check_call([sys.executable,'-m','pip','install',*missing])
PROJECT_ROOT = Path.cwd() / 'fso_v4_project'
PROJECT_ROOT.mkdir(exist_ok=True)
print('Project:', PROJECT_ROOT)''')
    add('markdown','## 2. Canonical source files\nThese cells are generated from the repository. To edit later, change the standalone source files and rebuild this notebook rather than maintaining two copies.')
    for file in FILES:
        body=(ROOT/file).read_text(encoding='utf-8')
        add('markdown',f'### `{file}`')
        add('code',f"p = PROJECT_ROOT / {file!r}\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text({body!r}, encoding='utf-8')\nprint('Wrote', p.relative_to(PROJECT_ROOT))")
    add('markdown','## 3. Run numerical regression tests\nThe run stops if any test fails. These tests verify the model implementation, not its empirical accuracy.')
    add('code', '''subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=PROJECT_ROOT,check=True)''')
    add('markdown','## 4. Run full experiments\nFull mode uses 100,000 samples per largest MC run and each multi-case run. Set `FAST_MODE=True` for 20,000 samples. Analytic results are unchanged.')
    add('code','''import os
FAST_MODE = False
subprocess.run([sys.executable,'run_study.py'],cwd=PROJECT_ROOT,env={**os.environ,'FAST_MODE':'1' if FAST_MODE else '0'},check=True)
subprocess.run([sys.executable,'verify_manifest.py'],cwd=PROJECT_ROOT,check=True)''')
    add('markdown','## 5. Inspect results\nThe three figures below compare both source conventions, atmospheric models and fog coefficient assumptions. All twelve figures and eleven CSV tables are exported.')
    add('code','''from IPython.display import display, Image
import csv
for name in ('10_optimization_convention_sensitivity','11_model_and_target_sensitivity','12_fog_model_benchmark'):
    display(Image(filename=str(PROJECT_ROOT/'results'/'figures'/(name+'.png'))))
with (PROJECT_ROOT/'results/tables/09_model_and_target_sensitivity.csv').open() as f:
    for row in csv.DictReader(f):
        if float(row['target']) == .92:
            print(row['profile'], 'TV='+row['tv_radius'], 'diameter_cm='+row['diameter_cm'], 'ceiling='+row['finite_aperture_ceiling'], row['status'])''')
    add('markdown','## 6. Export GitHub-ready update\nDownload `github_update.zip` from Colab Files. This archive uses repository-relative paths. Preserve existing LICENSE, CITATION.cff, `.git` and other assets. Review `UPDATE_GITHUB.md` before uploading.')
    add('code','''from zipfile import ZipFile, ZIP_DEFLATED
subprocess.run([sys.executable,'build_notebook.py'],cwd=PROJECT_ROOT,check=True)
archive=Path.cwd()/'github_update.zip'
with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=8) as z:
    for p in sorted(PROJECT_ROOT.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.pyc'):
            z.write(p,p.relative_to(PROJECT_ROOT).as_posix())
print('Ready:',archive)
# Optional in Google Colab:
# from google.colab import files; files.download(str(archive))''')
    return {'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python'}},'nbformat':4,'nbformat_minor':5}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();nb=build()
    if args.check:
        existing=json.loads(DEST.read_text())
        assert [(c['cell_type'],c['source']) for c in existing['cells']]==[(c['cell_type'],c['source']) for c in nb['cells']], 'Notebook source differs: regenerate with build_notebook.py'
        print('Notebook canonical sources verified')
    else:
        DEST.parent.mkdir(parents=True,exist_ok=True);DEST.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n',encoding='utf-8');print('Built',DEST)
