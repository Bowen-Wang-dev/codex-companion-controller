import hashlib
import json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
image = (root/'dist/PassportController.bin').read_bytes()
manifest = {'version': '0.2.11', 'chip': 'esp32c3', 'idf': '5.5.3', 'flash': 8388608,
            'size': len(image), 'sha256': hashlib.sha256(image).hexdigest(),
            'offset': 65536, 'writes': 'application only; live partition validation required',
            'bootloader_included': False, 'partition_table_included': False,
            'apple_assets_included': (root/'firmware/main/pet_assets.h').exists(),
            'codex_credentials_included': False}
(root/'dist/manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps(manifest, indent=2))
