#!/usr/bin/env python3
"""Package exact, verified existing UF2 files; never rebuild or flash a board."""
import argparse
from datetime import date
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import zipfile

here = Path(__file__).resolve().parent
firmware = next(p for p in here.parents if (p / 'config/west.yml').is_file())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('manifest', type=Path)
args = parser.parse_args()
manifest_path = args.manifest.resolve()
manifest = json.loads(manifest_path.read_text())
release = manifest['release']
if not re.fullmatch(r'[A-Za-z0-9._-]+', release):
    parser.error('Invalid release name')
spec = importlib.util.spec_from_file_location('uf2_verify', here / 'verify-dongle-uf2.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)
content = {}
for item in manifest['files']:
    name = item['bundle_name']
    if name not in {'dongle.uf2', 'left.uf2', 'right.uf2'} or name in content:
        parser.error('Expected three distinct role-specific UF2 names')
    source = (firmware / item['local_path']).resolve()
    if not source.is_relative_to(firmware):
        parser.error('Source must be inside the firmware workspace')
    verifier.verify(source)
    data = source.read_bytes()
    if hashlib.sha256(data).hexdigest() != item['sha256']:
        parser.error(f'Hash mismatch: {source}')
    content[name] = data
if set(content) != {'dongle.uf2', 'left.uf2', 'right.uf2'}:
    parser.error('Missing firmware role')
content['manifest.json'] = manifest_path.read_bytes()
content['README.md'] = (manifest_path.parent / 'bundle-guide.md').read_bytes()
content['SHA256SUMS'] = ''.join(
    f'{hashlib.sha256(data).hexdigest()}  {name}\n'
    for name, data in sorted(content.items())
).encode()
created = date.fromisoformat(manifest['created_on'])
output = firmware / 'build/releases' / release
output.mkdir(parents=True, exist_ok=True)
bundle = output / f'prospector-touch-{release}.zip'
with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name, data in sorted(content.items()):
        entry = zipfile.ZipInfo(name, date_time=(created.year, created.month, created.day, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, data)
with zipfile.ZipFile(bundle) as archive:
    assert set(archive.namelist()) == set(content)
    for name, data in content.items():
        assert archive.read(name) == data
digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
bundle.with_suffix('.zip.sha256').write_text(f'{digest}  {bundle.name}\n')
print(f'PASS package round-trip: {bundle}\nSHA256 {digest}')
