# sketches

Combined gallery for three 100-day projects.

| Section | Source repo (branch) | Local folder |
|---|---|---|
| three.js (2022) | hobg0blin/three_hundred_days (`claude/static-threejs-conversion-5Zkb7`) | `~/projects/sketches-build/three_hundred_days` (8.7G, kept on the Linux disk) |
| website (2022) | hobg0blin/three_js_sketch_server (`claude/tender-volta-a48b8i`) | `three_js_sketch_server/` |
| loops (2023-24) | hobg0blin/100_days_of_loops (`claude/pensive-ritchie-4ptq44`) | `loops/` |

## Editing text

- `template.html` - the page (intro, styles). `{cards}` is where the grid goes.
- `sections/<series>.html` - intro block above each series (`loops`, `website`, `threejs`).
- `BROKEN` in `build.py` - sketches shown as "BROKEN" and not linked.

Then `python3 build.py` (a few seconds when only text changed).

## Full build

1. Build each project once (slow, only needed when sketches change):
   - `three_hundred_days/build_static.sh` -> `static/` (~25 min)
   - `three_js_sketch_server/build_static.sh` -> `static/`
   - `loops/docs/` is committed in that repo; `build_site.py` regenerates it.
2. `python3 build.py` -> `dist/`. Thumbnails come from each project's own media/screenshots,
   then `screenshots/`. Anything still missing is listed in `missing_thumbs.txt`.
3. To fill gaps: serve `dist/` (`python3 -m http.server 8080 -d dist`), then
   `CHROME=~/.cache/chrome-headless/chrome-headless-shell-linux64/chrome-headless-shell node screenshot.mjs`
   and re-run `build.py`.
4. Upload `dist/` to any static host.

Needs: python3, ffmpeg, rsync, node (+ `npm install`), git.
