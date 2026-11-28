"""Check exact bytes and SHA-256 of generated results and generating source."""
import json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parent
out=root/'results'
m=json.loads((out/'metadata/manifest.json').read_text())
assert set(p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file() and p.name!='manifest.json' and not p.name.startswith('.'))=={e['path'] for e in m['files']},'Result inventory mismatch'
for e in m['files']:
    b=(out/e['path']).read_bytes()
    assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],e['path']
for p,h in m['source_sha256'].items():
    assert hashlib.sha256((root/p).read_bytes()).hexdigest()==h,p
print(f"VERIFIED {len(m['files'])} result files and {len(m['source_sha256'])} generating source files")
