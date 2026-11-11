#!/usr/bin/env python3
"""Combine the three.js sketches, the 100 three.js days, and 100 Days of Loops into one
static site in dist/.

Expects each project to be built first:
  three_js_sketch_server/build_static.sh  -> three_js_sketch_server/static/
  three_hundred_days/build_static.sh      -> three_hundred_days/static/
  loops/build_site.py                     -> loops/docs/
"""
import hashlib
import html
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
THREE = ROOT / "three_js_sketch_server"
LOOPS = ROOT / "loops"
# Temporary: built on the Linux disk because the repo is 8.7G; final location TBD.
DAYS = Path.home() / "projects/sketches-build/three_hundred_days"
SHOTS = ROOT / "screenshots"
# Sketches that don't work at all (e.g. crash the browser): shown as BROKEN, not linked.
BROKEN = {"days/day31/", "three/sketch_scene_queueing_prototype/"}
SECTIONS = ROOT / "sections"  # optional per-series intro text: website.html, threejs.html, loops.html
MEDIA_RE =re.compile(r"\.(mp4|mov|webm|gif|png|jpe?g)$", re.I)

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def first_commit_date(repo, path):
    out = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%as", "--", path],
        cwd=repo, capture_output=True, text=True).stdout.split()
    return date.fromisoformat(out[-1]) if out else None


def make_thumb(src, dest):
    """Representative frame of a video/gif/image -> 640px-wide jpg (skipped if up to date)."""
    if dest.exists() and dest.stat().st_mtime >= src.stat().st_mtime:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
                    "-vf", "thumbnail,scale=640:-2", "-frames:v", "1", str(dest)], check=True)


def three_entries():
    entries = []
    for d in sorted((THREE / "static").glob("sketch_*")):
        name = d.name.removeprefix("sketch_")
        committed = first_commit_date(THREE, f"src/js/{d.name}")
        # Names like "11_10" or "oct_22" are dates, not titles; git supplies the year.
        m = re.fullmatch(r"(\d{1,2}|[a-z]{3})_(\d{1,2})", name)
        if m and committed:
            month = MONTHS.get(m[1]) or int(m[1])
            when, title = date(committed.year, month, int(m[2])), None
        else:
            when, title = committed, name.replace("_", " ")
        shot = THREE / "src/public/screenshots" / f"{d.name}.jpg"
        thumb = None
        if shot.exists():
            thumb = f"thumbs/three-{shot.name}"
            (DIST / "thumbs").mkdir(exist_ok=True)
            shutil.copy(shot, DIST / thumb)
        entries.append(dict(series="website", num=None, title=title, date=when,
                            href=f"three/{d.name}/", thumb=thumb))
    return entries


def days_entries():
    entries = []
    seen = set()  # media files got copied forward when a day's folder was duplicated
    days = sorted((DAYS / "static").glob("day[0-9]*"), key=lambda d: int(d.name[3:]))
    for d in days:
        num = int(d.name.removeprefix("day"))
        media = sorted(f for f in (DAYS / d.name).iterdir() if MEDIA_RE.search(f.name))
        thumb = None
        if media:
            digest = hashlib.md5(media[0].read_bytes()).hexdigest()
            if digest not in seen:  # only the first day with a given file uses it
                seen.add(digest)
                thumb = f"thumbs/days-{num:03d}.jpg"
                make_thumb(media[0], DIST / thumb)
        entries.append(dict(series="threejs", num=num, title=f"threejs {num:03d}",
                            date=first_commit_date(DAYS, d.name),
                            href=f"days/{d.name}/", thumb=thumb))
    return entries


def loops_entries():
    entries = []
    for d in sorted(LOOPS.glob("[0-9][0-9][0-9]_*")):
        num, _, name = d.name.partition("_")
        thumb = LOOPS / "docs/assets" / num / "_thumb.jpg"
        entries.append(dict(
            series="loops", num=int(num),
            title=f"{name.replace('_', ' ')} (loops {num})",
            date=first_commit_date(LOOPS, d.name),
            href=f"loops/#{num}",
            thumb=f"loops/assets/{num}/_thumb.jpg" if thumb.exists() else None))
    return entries


def sort_entries(entries):
    """Newest first. Series are ordered by their latest date; within a numbered series the
    number wins over commit dates (several days were often committed together)."""
    latest = {}
    for e in entries:
        if e["date"]:
            latest[e["series"]] = max(latest.get(e["series"], date.min), e["date"])

    def key(e):
        within = e["num"] if e["num"] is not None else (e["date"] or date.min).toordinal()
        return (latest.get(e["series"], date.min), within)

    return sorted(entries, key=key, reverse=True)


def fill_from_screenshots(entries):
    """Use screenshots/ (made by screenshot.mjs) for entries with no thumbnail, and list
    the ones still missing in missing_thumbs.txt for screenshot.mjs to capture."""
    missing = []
    for e in entries:
        if e["thumb"] or e["href"] in BROKEN:
            continue
        name = re.sub(r"[^\w]+", "-", e["href"]).strip("-") + ".jpg"
        shot = SHOTS / name
        if shot.exists():
            e["thumb"] = f"shots/{name}"
            (DIST / "shots").mkdir(exist_ok=True)
            shutil.copy(shot, DIST / e["thumb"])
        else:
            missing.append(f'{e["href"]}\t{name}')
    (ROOT / "missing_thumbs.txt").write_text("\n".join(missing) + "\n")
    print(f"{len(missing)} without thumbnails (see missing_thumbs.txt)")


def render_cards(entries):
    """Cards in order, with sections/<series>.html (if present) before each series' first card."""
    out, seen = [], set()
    for e in entries:
        if e["series"] not in seen:
            seen.add(e["series"])
            intro = SECTIONS / f'{e["series"]}.html'
            if intro.exists():
                out.append(f'<div class="section" id="{e["series"]}">{intro.read_text()}</div>')
        out.append(card(e))
    return "\n".join(out)


def card(e):
    if e["href"] in BROKEN:
        title = f'<span class="title">{html.escape(e["title"] or "")}</span>'
        return f'<div class="card"><div class="noimg broken">BROKEN</div>{title}<span class="date">{e["date"]:%-m/%-d/%Y}</span></div>'
    img = (f'<img src="{e["thumb"]}" loading="lazy" alt="">' if e["thumb"]
           else '<div class="noimg"></div>')
    title = f'<span class="title">{html.escape(e["title"])}</span>' if e["title"] else ""
    when = e["date"].strftime("%-m/%-d/%Y") if e["date"] else ""
    return f'<a href="{e["href"]}">{img}{title}<span class="date">{when}</span></a>'




def patch_loops_close():
    """Closing a loop's detail view returns to the main page instead of the loops gallery."""
    page = DIST / "loops/index.html"
    s = page.read_text()
    old = "function close(){ modal.classList.remove('open'); history.replaceState(null,'',location.pathname); }"
    new = ("function close(){ if (document.referrer.startsWith(location.origin + '/') "
           "&& !document.referrer.includes('/loops/')) history.back(); else location.href = '../#loops'; }")
    if old in s:
        page.write_text(s.replace(old, new))


def main():
    # rsync only copies what changed, so re-running after template/notes edits is quick.
    # Generated thumbnails live in dist/thumbs and dist/shots, outside the mirrored dirs.
    DIST.mkdir(exist_ok=True)
    for src, dest in [(THREE / "static", "three"), (DAYS / "static", "days"), (LOOPS / "docs", "loops")]:
        subprocess.run(["rsync", "-a", "--delete", f"{src}/", str(DIST / dest)], check=True)
    patch_loops_close()
    entries = sort_entries(three_entries() + days_entries() + loops_entries())
    fill_from_screenshots(entries)
    page = (ROOT / "template.html").read_text()
    (DIST / "index.html").write_text(page.replace("{cards}", render_cards(entries)))
    print(f"{len(entries)} sketches -> {DIST}")


if __name__ == "__main__":
    main()
