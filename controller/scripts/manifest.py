"""Describe the actual application image and its compiled UI language."""
import hashlib
import json
from pathlib import Path
import re
from firmware_update import image_language, source_digest


def build_manifest(root):
    image = (root/'dist/PassportController.bin').read_bytes()
    version = re.search(r'set\(PROJECT_VER "companion-([^"]+)"\)',
                        (root/'firmware/CMakeLists.txt').read_text(encoding='utf-8')).group(1)
    return {'version': version, 'chip': 'esp32c3', 'idf': '5.5.3', 'flash': 8388608,
            'size': len(image), 'sha256': hashlib.sha256(image).hexdigest(),
            'ui_language': image_language(image),
            'offset': 65536, 'writes': 'application only; live partition validation required',
            'bootloader_included': False, 'partition_table_included': False,
            'apple_assets_included': (root/'firmware/main/pet_assets.h').exists(),
            'codex_credentials_included': False, 'source_sha256': source_digest(root)}


if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    manifest=build_manifest(root)
    (root/'dist/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(manifest,indent=2))
