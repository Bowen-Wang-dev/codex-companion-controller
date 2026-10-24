#!/usr/bin/env python3
"""Resize user-supplied, authorized Apple originals into flash-resident RGB565. No downloading/drawing."""
import argparse
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--local-system-render', action='store_true', help='Private prototype from macOS system rendering; no distribution license asserted')
parser.add_argument('--rights-file', type=Path,
                    help='JSON: apple_original=true and rights_basis describing your permission')
args = parser.parse_args()
if args.local_system_render:
    if args.source.resolve() != (Path(__file__).resolve().parents[1]/'private/apple-originals').resolve():
        parser.error('Local render mode only accepts private/apple-originals')
    rights={'source':'Local macOS Apple Color Emoji rendering', 'distribution_license':'NOT established; do not redistribute generated assets or binary'}
else:
    if not args.rights_file: parser.error('--rights-file required for imported third-party images')
    rights=json.loads(args.rights_file.read_text())
    if rights.get('apple_original') is not True or not rights.get('rights_basis','').strip(): parser.error('Need original Apple assets and rights basis')
from PIL import Image, ImageOps
root = Path(__file__).resolve().parents[1]
parts = ['idle', 'working', 'permission', 'delight', 'crying', 'completed', 'neutral', 'palms']
images = {}
for name in parts:
    with Image.open(args.source/(name+'.png')) as image:
        images[name] = image.convert('RGBA')
output = ['#pragma once', '#include "lvgl.h"', '#include <string.h>']
for name in parts[:6]+['exhausted']:
    canvas = Image.new('RGB', (96, 96), (0, 0, 0))
    if name == 'exhausted':
        for part, x in [('neutral', 0), ('palms', 49)]:
            resized = ImageOps.contain(images[part], (47, 80), Image.Resampling.LANCZOS)
            canvas.paste(resized, (x+(47-resized.width)//2, (96-resized.height)//2), resized)
    else:
        resized = ImageOps.contain(images[name], (96, 96), Image.Resampling.LANCZOS)
        canvas.paste(resized, ((96-resized.width)//2, (96-resized.height)//2), resized)
    raw = bytearray()
    for r, g, b in canvas.getdata():
        value = ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
        raw.extend((value & 255, value >> 8))
    output.append(f'static const uint8_t pixels_{name}[] = {{')
    for i in range(0, len(raw), 32):
        output.append(','.join(str(v) for v in raw[i:i+32])+',')
    output.append('};')
    output.append(f'static const lv_image_dsc_t asset_{name} = {{ .header = {{ .magic=LV_IMAGE_HEADER_MAGIC, .cf=LV_COLOR_FORMAT_RGB565, .w=96, .h=96, .stride=192 }}, .data_size=18432, .data=pixels_{name} }};')
output.append('static const lv_image_dsc_t *pet_asset(const char *state) {')
for name in parts[:6]+['exhausted']:
    output.append(f'if(!strcmp(state,"{name}"))return &asset_{name};')
output.append('return &asset_idle; }')
(root/'firmware/main/pet_assets.h').write_text('\n'.join(output))
(root/'assets/generated').mkdir(exist_ok=True)
(root/'assets/generated/rights.json').write_text(json.dumps(rights,indent=2))
print('Imported originals; no replacement Emoji generated. Rebuild firmware.')
