"""Append supplied records without changing existing lots or duplicating source URLs."""
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
import hashlib
import json
import shutil


def identity(source):
    url = urlsplit(source['url'])
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip('/'), url.query, ''))


def merge(root, source):
    data = root / '_catalogue'
    lots = json.loads((data / 'lots.json').read_text())
    sources = json.loads((data / 'sources.json').read_text())
    incoming = json.loads((source / 'lots.json').read_text())
    evidence = json.loads((source / 'sources.json').read_text())
    by_id = {lot['id']: lot for lot in lots}
    by_source = {identity(sources[lot['id']]): lot['id'] for lot in lots}
    assert len(by_id) == len(by_source) == len(lots), 'Existing catalogue contains duplicates'
    additions, files, skipped = [], [], []
    # Validate the entire import before writing anything.
    for lot in incoming:
        key = lot['id']
        src = evidence[key]
        origin = identity(src)
        if key in by_id:
            assert by_id[key] == lot and sources[key] == src, f'Existing record conflict: {key}'
            continue
        if origin in by_source:
            skipped.append(key)
            continue
        assert lot['status'] == 'closed', f'Review source availability: {key}'
        assert set(lot['images']) == {image['path'] for image in src['images']}, key
        for image in src['images']:
            path = Path(image['path'])
            assert not path.is_absolute() and '..' not in path.parts and path.parts[0] == 'img', path
            original, target = source / path, root / path
            assert hashlib.sha256(original.read_bytes()).hexdigest() == image['sha256'], path
            if target.exists():
                assert target.read_bytes() == original.read_bytes(), f'Image conflict: {path}'
            else:
                files.append((original, target))
        additions.append(lot)
        by_id[key], by_source[origin], sources[key] = lot, key, src
    for original, target in files:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(original, target)
    if additions:
        (data / 'lots.json').write_text(json.dumps(lots + additions, ensure_ascii=False, indent=2) + '\n')
        (data / 'sources.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n')
    print(f'Imported {len(additions)} new lots and {len(files)} new images; skipped {len(skipped)} duplicate sources.')
    return [lot['id'] for lot in additions]
