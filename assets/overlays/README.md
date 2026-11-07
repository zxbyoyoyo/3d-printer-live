# Transparent live overlays

`glove.png` and `heart.png` are original assets generated with the built-in ImageGen tool on 2026-11-07. Both retain true alpha transparency. The hand is deliberately a generic white cartoon glove; no platform interface is included.

Generation prompts:

- Glove: "A single isolated white cartoon glove hand sticker for a livestream overlay on a truly transparent background. One index finger points straight down, rounded other fingers curled, thumb to the right, wrist cuff at top, clean charcoal outline and soft gray cel shading. No text, arrows, border, screenshot UI or checkerboard."
- Heart: "A single high-resolution livestream gift sticker on a genuinely transparent background. A plump glossy hot-pink heart above a larger soft pink heart, with a tilted lavender-blue orbit ring around the base. Candy/jelly 3D rendering, soft highlights, no text, watermark, hand or frame."

`point-down` and `heart-reminder` animations are assembled from these originals by `scripts/build-overlays.py`. Both are 40 frames, 2 seconds, infinite loop. GIF uses binary transparency with disposal=2; lossless WebP preserves soft alpha. Their text and the static rules PNG use the default printing rules. No checkerboard is baked into the artwork.

The small heart, beer and lollipop used in the rules card are reused from upstream `assets/generated/original-icons/`, under the repository's existing MIT license. See `docs/MAC-使用说明.md` for usage and custom rule export.
