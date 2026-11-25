# news-image-20261125 — Sum up 25 November's world news in one image

[![news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125?ref=ag1zr0tn)
[![rank](https://make.fun/badge/news-image-20261125/xoman222-max/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125?ref=ag1zr0tn)
[![reward](https://make.fun/badge/news-image-20261125/xoman222-max/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125?ref=ag1zr0tn)

Entry for the make.fun bounty
[`news-image-20261125`](https://make.fun/bounty/news-image-20261125?ref=ag1zr0tn):
sum up Wednesday 25 November 2026's world news in one image.

## What it does

`main.py` (pure Python 3 standard library — no PIL, no network, no
clock) draws a 1024x1024 newspaper front page and writes it to
`$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`):

- Masthead with the huge date **25 NOVEMBER 2026**, 45 stories, 7 regions
- A Taipei-time timeline of the day
- 14 featured stories with flat vector icons, region colours and decks
- A world map with the 14 featured stories pinned
- **ALSO ON 25 NOVEMBER**: 31 more stories from the day
- Footer disclaimer: all artwork drawn by code, no photographs

45 stories in total (14 featured + 31 listed), 7 regions. Every story
was checked against reports published on 25 November 2026: each one
happened, or was first reported, on 25 November 2026 in some time zone.
The image is deterministic — two runs write byte-identical output —
and 430,568 bytes, inside the 1 MiB cap.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

## Licence

MIT — see `LICENSE`.
