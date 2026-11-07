#!/usr/bin/env python3
"""Build looping alpha WebP/GIF overlays from the supplied original PNG assets.

Requires Pillow. Set OVERLAY_FONT to a bold CJK font on other systems.
GIF has binary alpha; animated WebP/browser overlays retain soft alpha edges.
"""
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets/overlays'
PINGFANG = list(Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font7').glob('*/AssetData/PingFang.ttc'))
FONT_CANDIDATES = [os.environ.get('OVERLAY_FONT', ''), *map(str, PINGFANG), '/System/Library/Fonts/STHeiti Medium.ttc',
                   '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 'C:/Windows/Fonts/msyhbd.ttc']
FONT = next((p for p in FONT_CANDIDATES if p and Path(p).is_file()), None)
if not FONT:
    raise SystemExit('Set OVERLAY_FONT to an installed bold Chinese font.')

def fitted(source, size):
    return ImageOps.contain(source, size, Image.Resampling.LANCZOS)

def centered(canvas, image, cx, y):
    canvas.alpha_composite(image, (round(cx - image.width / 2), round(y)))

def text(canvas, label, xy, size, anchor='mm'):
    draw = ImageDraw.Draw(canvas)
    draw.text(xy, label, font=ImageFont.truetype(FONT, size, index=11 if 'PingFang' in FONT else 0), anchor=anchor,
              fill='#ffe327', stroke_width=2, stroke_fill='#694a0c')

def save_animation(name, frames):
    frames[0].save(OUT / (name + '.webp'), save_all=True, append_images=frames[1:],
                   duration=50, loop=0, lossless=True, method=4)
    # Reserve palette index 255 for transparent pixels and dispose every frame,
    # so the hand does not leave trails on OBS or dark video backgrounds.
    rgb_frames = [frame.convert('RGB') for frame in frames]
    sheet = Image.new('RGB', (frames[0].width, frames[0].height * len(frames)))
    for i, frame in enumerate(rgb_frames):
        sheet.paste(frame, (0, i * frame.height))
    palette = sheet.quantize(colors=255)
    gif_frames = []
    for frame in frames:
        indexed = frame.convert('RGB').quantize(palette=palette, dither=Image.Dither.NONE)
        indexed.paste(255, mask=frame.getchannel('A').point(lambda alpha: 255 if alpha < 128 else 0))
        indexed.info['transparency'] = 255
        gif_frames.append(indexed)
    gif_frames[0].save(OUT / (name + '.gif'), save_all=True, append_images=gif_frames[1:],
                      duration=50, loop=0, transparency=255, disposal=2, optimize=False)

hand = Image.open(OUT / 'glove.png').convert('RGBA')
heart = Image.open(OUT / 'heart.png').convert('RGBA')
# The static originals keep their source alpha; fitting below creates animation frames.
point_frames, heart_frames = [], []
for i in range(40):
    t = i / 40
    point = Image.new('RGBA', (360, 480))
    bob = 22 * math.sin(math.pi * t * 2) ** 2
    centered(point, fitted(hand, (300, 380)), 180, 22 + bob)
    point_frames.append(point)
    frame = Image.new('RGBA', (480, 660))
    pulse = 1 + .055 * math.sin(4 * math.pi * t) * max(0, math.sin(2 * math.pi * t))
    centered(frame, fitted(heart, (round(245 * pulse), round(245 * pulse))), 240, 15 - 7 * (pulse - 1))
    text(frame, '送个小心心', (240, 302), 60)
    text(frame, '打印大图一张', (240, 371), 42)
    centered(frame, fitted(hand, (195, 230)), 240, 402 + bob)
    heart_frames.append(frame)
save_animation('point-down', point_frames)
save_animation('heart-reminder', heart_frames)

rules = Image.new('RGBA', (1200, 1040))
text(rules, '评论 666 打印小图一张', (44, 152), 98, 'lm')
for i, (icon, label) in enumerate([('heart', '打印大图一张'), ('beer', '打印大图两张'), ('lollipop', '打印大图三张')], start=1):
    image = fitted(Image.open(ROOT / f'assets/generated/original-icons/{icon}.png').convert('RGBA'), (208, 208))
    centered(rules, image, 148, 32 + i * 240 + (240 - image.height) / 2)
    text(rules, label, (292, 152 + i * 240), 116, 'lm')
rules.save(OUT / 'print-rules.png')
print('Created 2 transparent loop animations (GIF + WebP) and print-rules.png')
