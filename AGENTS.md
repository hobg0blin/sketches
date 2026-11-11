# sketches - agent notes

See README.md for layout, build and deploy steps.

- Deploy: `deploy.sh` is local-only and gitignored; never commit server names, IPs or paths.
- WSL quirk: renaming/moving folders on /mnt/c from WSL can leave a stale `d?????????` entry;
  renaming from Windows (cmd `ren`) to a new name fixes it.

## Changelog

- 11/11/2026 (Claude Opus 5.5): Combined the three projects into one page. build.py (incremental rsync,
  ffmpeg thumbs deduped by file hash, numeric sort within series, section blocks, BROKEN list,
  loops modal closes to homepage), screenshot.mjs (headless Chrome, fresh browser per sketch),
  template.html, sections/. Fixed unquoted ammo.js path in three_hundred_days/build_static.sh
  (local change, not pushed).
