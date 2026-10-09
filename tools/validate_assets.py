"""Validate local PNG manifest metadata against generated files (no dependencies)."""
from pathlib import Path
import json, struct
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'frontend/assets/manifest.json').read_text(encoding='utf8'))
assets=manifest['assets']
seen=set()
for asset_id,item in assets.items():
    assert asset_id==item['asset_id'],asset_id
    assert item['file']==item['path'],asset_id
    assert item['file'] not in seen,asset_id
    seen.add(item['file'])
    path=ROOT/'frontend'/item['file']
    assert path.is_file(),str(path)
    content=path.read_bytes()
    assert content[:8]==b'\x89PNG\r\n\x1a\n',str(path)
    width,height=struct.unpack('>II',content[16:24])
    assert (width,height)==(item['width'],item['height']),asset_id
    assert width%item['frame_width']==0 and height%item['frame_height']==0,asset_id
    assert len(item['frames'])>=1,asset_id
    assert item['source'] and item['license'],asset_id
print(f'{len(assets)} assets verified: correct PNG sizes, frame alignment, IDs, metadata.')
